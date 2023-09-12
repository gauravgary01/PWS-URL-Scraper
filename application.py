from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen as uReq
import logging
import pymongo
logging.basicConfig(filename="scraper.log" , level=logging.INFO)
import os
import re
import pandas as pd
import csv


application = Flask(__name__)

app = application

@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            # channel name to search details for 
            query = request.form['content'].replace(" ", "")

            # directory to store CSVs
            save_directory = "CSVs/"
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            #fake user agent to avoid getting blocked by Google
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}

            #fetch the channel's videos page
            response = requests.get(f"https://www.youtube.com/@{query}/videos", headers= headers)

            #parse the HTML using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            response_text = response.text

            vid_links = re.findall(r"watch\?v=[A-Za-z0-9_-]{11}", response_text)
            vid_thumbnails = re.findall(r"https://i.ytimg.com/vi/[A-Za-z0-9_-]{11}/[A-Za-z0-9_]{9}.jpg", response_text)
            vid_titles = re.findall('"title":{"runs":\[{"text":".*?"', response_text)

            pattern3 = re.compile(r"[0-9]+(\.[0-9]+)?[a-zA-Z]*K views")  # view count
            pattern4 = re.compile(r"\d+ (minutes|hours|hour|days|day|weeks|week|years|year) ago")  # vedio age

            matches1 = pattern3.finditer(response_text)
            matches2 = pattern4.finditer(response_text)

            vid_viewcounts=[]
            vid_ages=[]
            count = 0
            for match1,match2 in zip(matches1,matches2):
                vid_ages.append(match2[0])
                vid_viewcounts.append(match1[0])
            
            titles = vid_titles[0:5]
            thumbnails = list(dict.fromkeys(vid_thumbnails))
            links = vid_links[0:5]
            viewcounts=vid_viewcounts[0:10:2]
            ages=vid_ages[0:10:2]

            details_list=[]

            for title,thumbnail,link,viewcount,age in zip(titles,thumbnails,links,viewcounts,ages):
                details_dict={
                    "title":str(title.split('"')[-2]),
                    "thumbnail": str(thumbnail),
                    "link": "https://www.youtube.com/"+str(link),
                    "viewcount": str(viewcount),
                    "age": str(age)
                }
                details_list.append(details_dict)

            # Save the details_list to a CSV file
            with open("output.csv", "w", newline="", encoding="utf-8") as csv_file:
                fieldnames = ["title", "thumbnail", "link", "viewcount", "age"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
                # Write the header row
                writer.writeheader()
    
                # Write the data rows
                for details_dict in details_list:
                    writer.writerow(details_dict)

            client = pymongo.MongoClient("mongodb+srv://gauravgary01:MMNNBBVVCCXXZZ@cluster0.b2c97d9.mongodb.net/?retryWrites=true&w=majority")
            db = client['channel_scrape']
            review_col = db['channel_scrape_data']
            review_col.insert_many(details_list)

            return render_template('result.html', reviews= details_list)
        
        except Exception as e:
            logging.info(e)
            return 'something is wrong'


if __name__ == '__main__':
    app.run(host='0.0.0.0')