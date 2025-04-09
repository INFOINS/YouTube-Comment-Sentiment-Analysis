from flask import Flask
from pytube import YouTube
import pandas as pd
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


# def get_replies(comment_id, token):
#   replies_response = yt_object.comments().list(part='snippet',
#                                                maxResults=100,
#                                                parentId=comment_id,
#                                                pageToken=token).execute()

#   for reply in replies_response['items']:
#     all_comments.append(reply['snippet']['textDisplay'])

#   if replies_response.get("nextPageToken"):
#     return get_replies(comment_id, replies_response['nextPageToken'])
#   else:
#     return []


# def get_comments(youtube, video_id, next_view_token):
#   global all_comments

#   # check for token
#   if len(next_view_token.strip()) == 0:
#     all_comments = []

#   if next_view_token == '':
#     # get the initial response
#     comment_list = youtube.commentThreads().list(part='snippet',
#                                                  maxResults=100,
#                                                  videoId=video_id,
#                                                  order='relevance').execute()
#   else:
#     # get the next page response
#     comment_list = youtube.commentThreads().list(
#         part='snippet',
#         maxResults=100,
#         videoId=video_id,
#         order='relevance',
#         pageToken=next_view_token).execute()
#   # loop through all top level comments
#   for comment in comment_list['items']:
#     # add comment to list
#     all_comments.append(
#         [comment['snippet']['topLevelComment']['snippet']['textDisplay']])
#     # get number of replies
#     reply_count = comment['snippet']['totalReplyCount']
#     all_replies = []
#     # if replies greater than 0
#     if reply_count > 0:
#       # get first 100 replies
#       replies_list = youtube.comments().list(part='snippet',
#                                              maxResults=100,
#                                              parentId=comment['id']).execute()
#       for reply in replies_list['items']:
#         # add reply to list
#         all_replies.append(reply['snippet']['textDisplay'])

#       # check for more replies
#       while "nextPageToken" in replies_list:
#         token_reply = replies_list['nextPageToken']
#         # get next set of 100 replies
#         replies_list = youtube.comments().list(
#             part='snippet',
#             maxResults=100,
#             parentId=comment['id'],
#             pageToken=token_reply).execute()
#         for reply in replies_list['items']:
#           # add reply to list
#           all_replies.append(reply['snippet']['textDisplay'])

#     # add all replies to the comment
#     all_comments[-1].append(all_replies)

#   if "nextPageToken" in comment_list:
#     print("have comment")
#     return get_comments(youtube, video_id, comment_list['nextPageToken'])
#   else:
#     print("not comment")
#     return []


def translate_text(text, target_language='en'):
  global positive_count
  global negative_count
  global neutral_count

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
      word for word in tokenized_text if word not in stopwords.words('english')
  ]
  lemmetize = WordNetLemmatizer()
  lemmatized_text = [lemmetize.lemmatize(word) for word in stop_words_remove]
  new_lemmatized_text = ' '.join(lemmatized_text)
  sentiment_analysis = SentimentIntensityAnalyzer()
  sentiment_score = sentiment_analysis.polarity_scores(text2)

  #print(sentiment_score)

  sentiment_score = sentiment_score['compound']
  if sentiment_score > 0:
    sentiment = 'positive'
    sentiment_score = sentiment_score * 100
    sentiment_score = round(sentiment_score, 2)
    positive_count += 1

    #print(positive_count)
    #sentiment_score = str(sentiment_score) + '%'
    #print(sentiment_score)
  elif sentiment_score < 0:
    sentiment = 'negative'
    sentiment_score = sentiment_score * 100
    sentiment_score = round(sentiment_score, 2)
    negative_count += 1
    #print(negative_count)
    #sentiment_score = str(sentiment_score) + '%'
    #print(sentiment_score)
  else:
    sentiment = 'neutral'
    sentiment_score = sentiment_score * 100
    sentiment_score = round(sentiment_score, 2)
    neutral_count += 1
    #print(neutral_count)
    #sentiment_score = str(sentiment_score) + '%'
    #print(sentiment_score)

  #if text2 is not None:
  #return ' '.join(lemmatized_text)
  #return text2
  #else:
  #return ''  # Return an empty string if translation fails
