## Recommender service

Python movie recommender service
The recommender strategy is item-based, without paying attention to other users' histories.

Due to problems building dependencies, this program doesn't use requirements.txt, instead defining dependencies directly in the Dockerfile

* Listens on RabbitMQ queue "history"