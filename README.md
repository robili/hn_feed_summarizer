# Hacker news summarizer

I use Feedly as a RSS reader and for whatever reason I don't get the short blurb for HN posts. 

This script solves this for me by:

1) Pulling the articles (20 by default) from the official feed.
2) Sending the link to ChatGPT for summarization (150 tokens).
3) Adding the result to my own, personal feed.
4) Uploading the result to the web, where Feedly can pick it up.
