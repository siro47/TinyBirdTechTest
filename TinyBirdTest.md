# TinyHTTPDataHandlerServer Improvements

This document is containing the summary of the analysis I did for the technical test, the problems and improvements that I found for the code as well as the explanation of the changes I did in the code and why. Furthermore I am including some suggested architecture to make this system ready to scale in a production environment


# Initial Analysis

Taking a first look to the given code and the presented problem, those are the main issues I was concerned about when deploying this service to production and having to handle a high amount of concurrent requests.

## Web server performance 

It is important to check how a web server will behave in production under concurrent HTTP requests, handling multiprocessing, multithreading and so on. I have no previous experience using Tornado so I dig into their **documentation** and some **benchmarks** to check the motivations behind the decision.

It looks like is not the best web server available in terms of performance, but usually this is not the key point to choose a web server (readability, ease to code, utilities...) so if the goal is just to have a really small piece of code that processes requests as fast as possible maybe we should consider other alternatives, but if our goal is to build a more complex system then there is many other things to consider.

Anyway, as the technical test time is limited and our code is already running in production (as it is said in the README file) and any improvement will be really appreciated by our current customers I decided to **stick with the current web server choice** and apply the improvements I found in the doc to allow **multithreading processing**

## Use case coupling

Looking at the documentation several times, I could not find a clue about why are we doing this endpoint that converts our current information in ndjson to csv. 

Conversion is being made on the fly in each request, which usually only does makes sense for a service designed for an instant format converter for files or something similar, but storing the data in the same file than any other request received from any other user in the world? That looks like a centralized source of information which would require a total different approach like using a database to store the centralized data.

In that case I would create a **separate service** for ndjson file load and storage in our database and another one for reading the data from the database and generating the csv file. It is important to mark off who is going to consume this csv  to know the best way to implement this service (periodically, on demand or even at real time)

However, being this the second and maybe principal issue I spotted, the change is huge, so I decided to **postpone it to the further improvements section** and focus on some quick changes that can be deployed quickly and keep our current users happy with our service.

## Concurrent access to files

Now that our server is processing requests in multiple threads we are facing the problem that they are all accessing the same file, which will concur in some writing operations blocking others and some processes blocking others.

So I have decided that a quick approach to solve the problem is to make **each process write in a separate csv file** and only at the end **merge them using the os file system** that will manage the file as chunk pieces and be much more efficient. Also this approach will allow us not to merge the file at each process but on demand when the csv file is requested.

## Batch processing

The final problem spotted is that reading and writing lines are being handled **row per row** which is a very inefficient way to do it. I would assume we have to perform data validation so reading process would have to remain row per row, because it should be the one tied to the validation, but it will have a huge impact just to change the writing process (which is commonly the most expensive one) so
I have changed the **writing process** to a one **using batches** with configurable size. The test code is using the csv library which reports in its doc that there is a performance difference using batch processing but the same concept is applied if the system is migrated to a one writing into a database.

Maybe for this example with not so large files the impact is not so high, but handling larger files which is something common, the impact will be greater.

## Architecture

Once all this changes has been applied and our the application performance has been increased the next step should be designing an architecture that allow us to iterate new versions of our service easily.
I have followed **clean code architecture patterns** to split our app code into 3 different layers:

 - **API:** Contains every dependency of our web server, so migrating to a different web server only will need to make changes to this layer
 - **Domain:** Contain our domain logic. Not much in this example, but this layer will be transversal to technologies, we can apply unit test to this code, etc. etc.
 - **Storage:** Contain the storage logic that now is directly storing data in files, but will turn to be stored in a db in the future. Different connector can be written for different storage systems and only this layer needs to be changed for that

This architectural redesign has been added to a different branch in the repo called **clean_architecture** cause I have done a really quick approach with many improvements needed, but I think is enough to get an overall idea.

# Further improvements

Though this workaround solution can scale vertically taking advantage of all the cores of the host (and score pretty well in the example because we are running 8 simultaneuos processes and standard computers usually have 8 cores) the solution is not going to scale when the requests increase to several thousands and **we need  an architecture able to scale horizontally** in several hosts.

Another key fact to remark is that we are **handling the entire input files in the host memory**, something that usually is not a problem, cause it is easy to find a machine with several GB of RAM memory which is more than enough to handle files for most of the standard use cases, but taking into account products like TinyBird, this may not be enough, so just one request for an enormous file of e.g. 1TB will need a preprocessing step splitting that file in chunks manageable for a single service which will concur on hundreds of processes needed to satisfy a single user's request.

So this is a general approach of how I would implement a service with this characteristics so it can scale horizontally (though it would depend a lot of the use cases and needs of our product)
![TinyBirdTechTest Diagram](https://docs.google.com/drawings/d/e/2PACX-1vS8OH_Yniq8QW0PU7ow-6Dp8u_CdXvcPSt-25nAqJZeYI47OVSlxg1mxU6UDohLrCMvIV6bLeBuSf-k/pub?w=960&h=720)
