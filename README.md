<h1>Unkani</h1>
<p>A data platform for healthcare startups</p>

<h3>Unkani API</h3>
<p>See the unkani <a href=https://documenter.getpostman.com/view/1189270/unkani-api/6tW6Rmd>data services API </a>for more information</p>


<h3>Sessions</h3>
<p>
When configuration variable 'SERVER_SESSION' == True, sessions are stored as key-value pairs in Redis.
When configuration variable 'SERVER_SESSION' != True, sessions are stored in JTWS signed broser cookies
</p>

<h3>Redis</h3>
<p>run: ./run_redis.sh to setup and run a redis in memory data store with default settings on the localhost
Used for</p>
<ol>
<li>Session storage</li>
<li>API rate limiting</li>
<li>Celery task queue and broker (when enabled)</li>
</ol>