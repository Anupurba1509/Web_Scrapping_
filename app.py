from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import pymongo

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)
CORS(app)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            shopclues_url = f"https://www.shopclues.com/search?q={searchString}"
            uClient = uReq(shopclues_url)
            shopcluesPage = uClient.read()
            uClient.close()
            shopclues_html = bs(shopcluesPage, "html.parser")
            bigboxes = shopclues_html.findAll("div", {"class": "column col3 search_blocks"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.shopclues.com" + box.a["href"]
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {"class": "r_comm_info"})
            review_boxes = prod_html.find_all("div", {"class": "review_desc"})

            reviews = []
            for commentbox, review_box in zip(commentboxes, review_boxes):
                try:
                    name_div = commentbox.find_all('div', class_='r_by')
                    name = name_div[0].text.strip() if name_div else 'No Name'
                except Exception as e:
                    name = 'No Name'
                    logging.info(f"Name extraction error: {e}")

                try:
                    rating = commentbox.div.text.strip() if commentbox.div else 'No Rating'
                except Exception as e:
                    rating = 'No Rating'
                    logging.info(f"Rating extraction error: {e}")

                try:
                    custComment = review_box.p.text.strip() 
                except Exception as e:
                    custComment = 'No Comment'
                    logging.info(f"Comment extraction error: {e}")

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "Comment": custComment}
                reviews.append(mydict)

            logging.info(f"Final result: {reviews}")

            Client= pymongo.MongoClient("mongodb+srv://anu:anu@cluster0.rfk7etw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db=Client['scrapper_eng_pwskills']
            coll_pw_eng=db['scrapper_pwskills_eng']
            coll_pw_eng.insert_many(reviews)

            return render_template('result.html', reviews=reviews)

        except Exception as e:
            logging.error(f"Error in review extraction: {e}")
            return 'Something went wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0")