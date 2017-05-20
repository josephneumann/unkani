import os
import sys
import unittest

import coverage


def run():
    os.environ['FLASK_CONFIG'] = 'testing'

    # start coverage engine
    cov = coverage.coverage(branch=True, include=['app/*'], omit=['app/general.py', 'app/flask_sendgrid.py'])
    cov.start()

    # run tests
    tests = unittest.TestLoader().discover('tests')
    ok = unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful()

    # print coverage report
    cov.stop()
    cov.save()
    print('Coverage Summary: ')
    cov.report()
    basedir = os.path.abspath(os.path.dirname(__file__))
    covdir = os.path.join(basedir, 'tmp/coverage')
    print('HTML version: file://%s/index.html' % covdir)
    cov.erase()

    sys.exit(0 if ok else 1)
