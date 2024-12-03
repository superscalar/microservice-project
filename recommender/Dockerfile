FROM python:slim
WORKDIR /var/www
RUN apt update
RUN apt-get -y install build-essential cmake g++
RUN apt-get -y install git
RUN apt-get -y install python3-sklearn
ADD main.py .
ADD history.py .
ADD recommender.py .
ADD requirements.txt .
ADD movies_clean.csv .

# We need the latest version of msgspec, but it's not in pip's repositories yet
# It's a dependency of flask, so we can't do anything about this
RUN pip install git+https://github.com/jcrist/msgspec.git@main

RUN pip install pandas
RUN pip install pika==1.3.2
RUN pip install RapidFuzz==3.10.1
RUN pip install Flask==3.0.3
RUN pip install Flask-Session==0.8.0
RUN pip install scikit-learn

RUN apt-get -y remove --purge build-essential cmake g++ git
RUN apt-get -y autoremove

CMD ["sh", "-c", "flask --app main.py run -p $RECOMMENDER_PORT --host=0.0.0.0"]