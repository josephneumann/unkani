import functools
from app.api_v1.errors import *
import time
from app import redis
from flask import current_app, g
from app.api_v1.errors import too_many_requests


def rate_limit(limit, period):
    """This decorator implements rate limiting."""

    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if current_app.config['USE_RATE_LIMITS']:
                # generate a unique key to represent the decorated function and
                # the IP address of the client. Rate limiting counters are
                # maintained on each unique key.
                key = '{0}/{1}'.format(f.__name__, str(g.current_user.id))
                limiter = RateLimit(key, limit, period)

                # set the rate limit headers in g, so that they are picked up
                # by the after_request handler and attached to the response
                rate_limit_info = {
                    'X-RateLimit-Remaining': str(limiter.remaining
                                                 if limiter.remaining >= 0 else 0),
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Reset': str(limiter.reset)
                }
                g.headers = rate_limit_info

                # if the client went over the limit respond with a 429 status
                # code, else invoke the wrapped function
                if not limiter.allowed:
                    return too_many_requests(message='You have exceeded your request rate limit: {}'.format(rate_limit_info))

            # let the request through
            return f(*args, **kwargs)

        return wrapped

    return decorator


class FakeRedis(object):
    """Redis mock used for testing."""

    def __init__(self):
        self.v = {}
        self.last_key = None

    def pipeline(self):
        return self

    def incr(self, key):
        if self.v.get(key, None) is None:
            self.v[key] = 0
        self.v[key] += 1
        self.last_key = key

    def expireat(self, key, time):
        pass

    def execute(self):
        return [self.v[self.last_key]]


class RateLimit(object):
    expiration_window = 10

    def __init__(self, key_prefix, limit, period):
        global redis
        if redis is None and current_app.config['USE_RATE_LIMITS']:
            if current_app.config['TESTING']:
                redis = FakeRedis()
            else:
                redis = redis

        self.reset = (int(time.time()) // period) * period + period
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.period = period
        p = redis.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = p.execute()[0]

    @property
    def allowed(self):
        return self.current <= self.limit

    @property
    def remaining(self):
        return self.limit - self.current
