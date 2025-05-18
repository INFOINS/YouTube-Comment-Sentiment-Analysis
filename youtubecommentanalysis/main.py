from flask import Flask, render_template, request, redirect, url_for
from pytube import YouTube
from googleapiclient.discovery import build
import googleapiclient.discovery
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

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('vader_lexicon')

app = Flask(__name__)
yt_object = None
all_comments = []


class DataStore():
  key1 = 0
  key2 = 0
  key3 = 0
  url = ''
  views = 0
  video_title = ''
  comm = 0


class commentses():
  all_comments = []


com = commentses()
data = DataStore()


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/process', methods=['GET', 'POST'])
def process():

  if request.method == 'POST':
    f = open("comments.txt", 'w')
    f.close()
    video_url = request.form['url_input']
    # video_url = "https://youtu.be/FvnS3tba34I?si=S-MuHm7aZVKNfGjK"
    video_id = extract.video_id(video_url)
    data.video_title = YouTube(video_url).title
    data.views = YouTube(video_url).views
    api_key = ""
    print(video_id)

    # recursive function to get all replies in a comment thread
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

      # check for token
      if len(next_view_token.strip()) == 0:
        com.all_comments = []

      if next_view_token == '':
        # get the initial response
        comment_list = youtube.commentThreads().list(
            part='snippet',
            maxResults=100,
            videoId=video_id,
            order='relevance').execute()
      else:
        # get the next page response
        comment_list = youtube.commentThreads().list(
            part='snippet',
            maxResults=100,
            videoId=video_id,
            order='relevance',
            pageToken=next_view_token).execute()
      # loop through all top level comments
      for comment in comment_list['items']:
        # add comment to list
        com.all_comments.append(
            [comment['snippet']['topLevelComment']['snippet']['textDisplay']])
        # get number of replies
        reply_count = comment['snippet']['totalReplyCount']
        all_replies = []
        # if replies greater than 0
        if reply_count > 0:
          # get first 100 replies
          replies_list = youtube.comments().list(
              part='snippet', maxResults=100,
              parentId=comment['id']).execute()
          for reply in replies_list['items']:
            # add reply to list
            all_replies.append(reply['snippet']['textDisplay'])

          # check for more replies
          while "nextPageToken" in replies_list:
            token_reply = replies_list['nextPageToken']
            # get next set of 100 replies
            replies_list = youtube.comments().list(
                part='snippet',
                maxResults=100,
                parentId=comment['id'],
                pageToken=token_reply).execute()
            for reply in replies_list['items']:
              # add reply to list
              all_replies.append(reply['snippet']['textDisplay'])

        # add all replies to the comment
        com.all_comments[-1].append(all_replies)

      if "nextPageToken" in comment_list:
        print("have comment")
        return get_comments(youtube, video_id, comment_list['nextPageToken'])
      else:
        print("not comment")
        return []

    com.all_comments = []
    global yt_object
    # build a youtube object using our api key
    yt_object = build('youtube', 'v3', developerKey=api_key)
    # get all comments and repliesdef get_comments(youtube, video_id, next_view_token, yt_object):
    # rest of your code...
    try:
      comments = get_comments(yt_object, video_id, '')
      print("DONE comments")
    except:
      print("comments not run")

    f = open("comments.txt", 'a', encoding="utf-8")
    for comment, replies in com.all_comments:
      print(comment)
      print("\n")
      f.write(comment + '\n')
      f.write('')

    f.close()
    print("\n helll")

    def translate_text(text, target_language='en'):
      # global positive_count
      # global negative_count
      # global neutral_count

      emoji_convert = emoji.demojize(text)
      lower_text = emoji_convert.lower()
      remove_url = re.sub(
          r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''',
          " ", lower_text)
      soup = BeautifulSoup(remove_url, 'html.parser')
      text_without_tags = soup.get_text()

      translation = GoogleTranslator(
          source='auto', target=target_language).translate(text_without_tags)

      text1 = re.sub('\d+', '', translation)  # Remove digits
      text2 = re.sub('[^\w\s]', '', text1)  # Remove special characters except
      tokenized_text = nltk.word_tokenize(text2)
      stop_words_remove = [
          word for word in tokenized_text
          if word not in stopwords.words('english')
      ]
      lemmetize = WordNetLemmatizer()
      lemmatized_text = [
          lemmetize.lemmatize(word) for word in stop_words_remove
      ]
      new_lemmatized_text = ' '.join(lemmatized_text)
      sentiment_analysis = SentimentIntensityAnalyzer()
      sentiment_score = sentiment_analysis.polarity_scores(text2)

      sentiment_score = sentiment_score['compound']
      if sentiment_score > 0:
        sentiment = 'positive'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        data.key1 += 1

      elif sentiment_score < 0:
        sentiment = 'negative'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        data.key2 += 1

      
      else:
        sentiment = 'neutral'
        sentiment_score = sentiment_score * 100
        sentiment_score = round(sentiment_score, 2)
        data.key3 += 1


    comment_count = 0
    positive_count = 1
    negative_count = 1
    neutral_count = 1
    
    # Translate each comment to English and write translations to a new file
    with open('comments.txt', 'r', encoding='utf-8') as file:
      comments_new = file.readlines()

    with open('translated_comments_english.txt', 'w',
              encoding='utf-8') as output_file:
      for comment in comments_new:

        translate_text(comment)
        comment_count += 1


    data.comm = comment_count
    postive_percentage = round(data.key1 * 100 / comment_count, 2)
    negative_percentage = round(data.key2 * 100 / comment_count, 2)
    neutral_percentage = round(data.key3 * 100 / comment_count, 2)
  

    # pie chart
    labels = 'postive', 'negative', 'neutral'
    sizes = [postive_percentage, negative_percentage, neutral_percentage]
    colors = ['green', 'red', 'blue']
    explode = (0.1, 0, 0)
    
    print("set value")
    data.key1 = postive_percentage
    data.key2 = negative_percentage
    data.key3 = neutral_percentage
    print(data.key1)
    print(data.key2)
    print(data.key3)
    print("this is a data")
    return redirect("/show")
  print("view in process")
  return 'hello done'


@app.route('/show')
def show():
  return render_template('graph.html',
                         act1_per=data.key1,
                         act2_per=data.key2,
                         act3_per=data.key3,
                         act1='Positive',
                         act2='Negative',
                         video_title=data.video_title,
                         views=data.views,
                         comments=data.comm,
                         act3='Neutral')


if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True)





