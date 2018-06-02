# Congratulations!

You have successfully built a new test in the suite!

There are some remaining tasks to do before you are ready to open a pull request, however.

## Next Steps

1. Edit `benchmark_config.json`

You will need alter `benchmark_config.json` to have the appropriate end-points and port specified.

2. Create `$NAME.dockerfile`

This is the dockerfile that is built into a docker image and run when a benchmark test is run. Specifically, this file tells the suite how to build and start your test application.

You can create multiple implementations and they will all conform to `[name in benchmark_config.json].dockerfile`. For example, the `default` implementation in `benchmark_config.json` will be `$NAME.dockerfile`, but if you wanted to make another implementation that did only the database tests for MySQL, you could make `$NAME-mysql.dockerfile` and have an entry in your `benchmark_config.json` for `$NAME-mysql`.

3. Test your application

        $ ssgberk --mode verify --test $NAME

This will run the suite in `verify` mode for your test. This means that no benchmarks will be captured and we will test that we can hit your implementation end-points specified by `benchmark_config.json` and that the response is correct.

Once you are able to successfully run your test through our suite in this way **and** your test passes our validation, you may move on to the next step.

4. Add your test to `.travis.yml`

Edit `.travis.yml` to ensure that Travis-CI will automatically run our verification tests against your new test. This file is kept in alphabetical order, so find where `TESTDIR=$LANGUAGE/$NAME` should be inserted under `env > matrix` and put it there.

5. Fix this `README.md` and open a pull request

Starting on line 59 is your actual `README.md` that will sit with your test implementation. Update all the dummy values to their correct values so that when people visit your test in our Github repository, they will be greated with information on how your test implementation works and where to look for useful source code.

After you have the real `README.md` file in place, delete everything above line 59 and you are ready to open a pull request.

Thanks and Cheers!







# $DISPLAY_NAME Benchmarking Test

### Test Type Implementation Source Code

* [JSON](Relative/Path/To/Your/Source/File)


## Important Libraries
The tests were run with:
* [Software](https://www.example1.com/)
* [Example](http://www.example2.com/)

## Test URLs
### JSON

http://localhost:8080/json
