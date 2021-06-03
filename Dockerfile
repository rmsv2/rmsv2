FROM nikolaik/python-nodejs:latest

# Allows docker to cache installed dependencies between builds
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install -g bower

# Mounts the application code to the image
COPY . code
WORKDIR /code

# Install bower stuff for web ui
RUN cd /code/static/ ; bower install --allow-root
