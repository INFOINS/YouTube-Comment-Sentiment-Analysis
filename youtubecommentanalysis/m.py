from flask import Flask, render_template, request
from pytube import YouTube
from googleapiclient.discovery import build
from pytube import extract
from googletrans import Translator
from deep_translator import GoogleTranslator
import emoji
import re
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

app = Flask(_name_)

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('vader_lexicon')

def get_replies(comment_id, token):
    replies_response = yt_object.comments().list(part='snippet',
                                                 maxResults=100,
                                                 parentId=comment_id,
                                                 pageToken=token).execute()
    for reply in replies_response['items']:
        all_comments.append(reply['snippet']['textDisplay'])
    if replies_response.get("nextPageToken"):
        return get_replies(comment_id, replies_response['nextPageToken'])
    else:
        return []

def get_comments(youtube, video_id, next_view_token):
    global all_comments
    if len(next_view_token.strip()) == 0:
        all_comments = []

    if next_view_token == '':
        comment_list = youtube.commentThreads().list(part='snippet',
                                                     maxResults=100,
                                                     videoId=video_id,
                                                     order='relevance').execute()
    else:
        comment_list = youtube.commentThreads().list(
            part='snippet',
            maxResults=100,
            videoId=video_id,
            order='relevance',
            pageToken=next_view_token).execute()

    for comment in comment_list['items']:
        all_comments.append(
            [comment['snippet']['topLevelComment']['snippet']['textDisplay']])
        reply_count = comment['snippet']['totalReplyCount']
        all_replies = []

        if reply_count > 0:
            replies_list = youtube.comments().list(part='snippet',
                                                   maxResults=100,
                                                   parentId=comment['id']).execute()
            for reply in replies_list['items']:
                all_replies.append(reply['snippet']['textDisplay'])

            while "nextPageToken" in replies_list:
                token_reply = replies_list['nextPageToken']
                replies_list = youtube.comments().list(
                    part='snippet',
                    maxResults=100,
                    parentId=comment['id'],
                    pageToken=token_reply).execute()
                for reply in replies_list['items']:
                    all_replies.append(reply['snippet']['textDisplay'])

        all_comments[-1].append(all_replies)

    if "nextPageToken" in comment_list:
        return get_comments(youtube, video_id, comment_list['nextPageToken'])
    else:
        return []

all_comments = []
yt_object = None  # Define globally

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        comments, sentiment_data = process_video(video_url)
        return render_template('graph.html', comments=comments, sentiment_data=sentiment_data)

    return render_template('index.html')

def process_video(video_url):
    global yt_object
    video_id = extract.video_id(video_url)
    api_key = "AIzaSyBX-j_OWT4A89XfLIcai69C3WaoSR1H_6M"
    yt_object = build('youtube', 'v3', developerKey=api_key)

    all_comments = []
    comments = get_comments(yt_object, video_id, '')

    for comment, replies in all_comments:
        translate_text(comment)

    return all_comments, sentiment_data

def translate_text(text, target_language='en'):
    global positive_count, negative_count, neutral_count
    emoji_convert = emoji.demojize(text)
    lower_text = emoji_convert.lower()
    remove_url = re.sub(
        r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''',
        " ", lower_text)
    soup = BeautifulSoup(remove_url, 'html.parser')
    text_without_tags = soup.get_text()

    translation = GoogleTranslator(
        source='auto', target=target_language).translate(text_without_tags)

    text1 = re.sub('\d+', '', translation)  # Remove digits
    text2 = re.sub('[^\w\s]', '', text1)  # Remove special characters except
    tokenized_text = nltk.word_tokenize(text2)
    stop_words_remove = [
        word for word in tokenized_text if word not in stopwords.words('english')
    ]
    lemmetize = WordNetLemmatizer()
    lemmatized_text = [lemmetize.lemmatize(word) for word in stop_words_remove]
    new_lemmatized_text = ' '.join(lemmatized_text)
    sentiment_analysis = SentimentIntensityAnalyzer()
    sentiment_score = sentiment_analysis.polarity_scores(text2)

    sentiment_score = sentiment_score['compound']
    if sentiment_score > 0:
        sentiment = 'positive'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        positive_count += 1
    elif sentiment_score < 0:
        sentiment = 'negative'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        negative_count += 1
    else:
        sentiment = 'neutral'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        neutral_count += 1

comment_count = 0
positive_count = 0
negative_count = 0
neutral_count = 0
sentiment_data = None

with open('comments.txt', 'r', encoding='utf-8') as file:
    comments_new = file.readlines()

with open('translated_comments_english.txt', 'w',
          encoding='utf-8') as output_file:
    for comment in comments_new:
        translate_text(comment)
        comment_count += 1

postive_percentage = round(positive_count * 100 / comment_count, 2)
negative_percentage = round(negative_count * 100 / comment_count, 2)
neutral_percentage = round(neutral_count * 100 / comment_count, 2)

labels = 'positive', 'negative', 'neutral'
sizes = [postive_percentage, negative_percentage, neutral_percentage]
colors = ['green', 'red', 'blue']
explode = (0.1, 0, 0)

plt.pie(sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        shadow=True,
        startangle=140)
plt.axis('equal')
plt.title('Sentiment Analysis')
plt.savefig('static/pie_chart.png')  # Save