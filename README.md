# DSC180A_Assignment3

This assignment includes:

1.  A description of the experimental design and a summary of the results with code-generated figures and tables (report)

2.  Development of code to replicate the main result under consideration, using methodological best practices (code)

The report can be found [here](https://github.com/StephanieMoore14/DSC180A_A3/blob/master/03-moore-final-project.ipynb).

* * * * *

This project consists of the entire 'result replication' as a single
report and code artifact. It puts together work from
assignments 1 and 2, along with additional material from more recent
work.

### Part 1 (Report)

A report consisting of:
* An introduction to the problem.
* An introduction to the data and data generation process.
* A brief review of historical context.
* EDA, assessment of reliability of data, need for cleaning and
  justification for approach to cleaning. 
* Careful analysis in differences in stop rates.
* Careful analysis of post-stop outcomes.
* Explanation and calculation of Veil of Darkness experiment.
* Critique of the short comings of the VoD, and likely quantitative
  effect of those shortcomings on the results.
* Moving beyond the SDSU study by looking at main results
  year-after-year.
* Conclusion.

### Part 2 (Code)

Development of code that will run the replication from
end-to-end (data ingestion to generating the results that inform the
reports) using best-practices.

The code satisfies the following criteria:
* Conforms to the template structure of the methodology portion of the
  course.
* Uses configuration files to parameterize the inputs of your pipeline.
* Use a `run.py` file to put together the processing logic, using
  commandline targets.
* Is runnable on the DSMLP servers in an existing Docker Image (either on
  given to you (e.g. `ucsd-ets/scipy-ml`, or one created by you).
* Uses a small amount of versioned test data that quickly verifying the
  runnability of the project.
* Contains a configuration file `config/env.json` with the following
  information:
  * a key `docker-image` with the value a DockerHub path (e.g. the
    input of the `-i` flag when starting a container on the DSMLP
    server.
  * a key `output-paths` with the value a list of output files created
    (the files with the results of the replication).

Code outcomes:
1. Can be uploaded to a DSMLP server.
2. Includes a container that can be started using the specified Docker Image in
   the repository's `env.json`, which can run the following command: `python
   run.py test-project`
4. Running the above target will run the replication on a small
   amount of test data. 
