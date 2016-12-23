# -*- coding: utf-8 -*-

import os

from flask import Flask, Response, redirect, request
from slackweb import Slack
from stackexchange import DESC, Site, Sort, StackOverflow

try:
    import config
    se_key = config.stackexchange['api_key']
    post_url = config.slack['post_url']
except:
    se_key = os.environ.get('SE_KEY')
    post_url = os.environ.get('POST_URL')


if not (se_key and post_url):
    import sys
    print 'No config.py file found. Exiting...'
    sys.exit(0)


MAX_QUESTIONS = 5


app = Flask(__name__)
so = Site(StackOverflow, se_key)
slack = Slack(url=post_url)


def get_response_string(q):
    q_data = q.json
    check = ' :white_check_mark:' if q.json['is_answered'] else ''
    return "|{0:d}|{1} <{2}|{3}> ({4:d} answers)".format(
        q_data['score'], check, q.url, q.title, q_data['answer_count'])


@app.route('/overflow', methods=['post'])
def overflow():
    """
    Example:
        /overflow python list comprehension
    """
    text = request.values.get('text')
    user = request.values.get('user_name')

    def channel():
        channel_name = request.values.get('channel_name')
        if channel_name == 'directmessage':
            return "@" + request.values.get('user_name')
        elif channel_name == 'privategroup':
            return request.values.get('channel_id')
        else:
            return "#" + channel_name

    try:
        qs = so.search(intitle=text, sort=Sort.Votes, order=DESC)
    except UnicodeEncodeError:
        return Response(('Only English language is supported. '
                         '{0} is not valid input.'.format(text)),
                        content_type='text/plain; charset=utf-8')

    resp_qs = ['# {0}\nStack Overflow Top Questions for "{1}"\n'.format(
               user, text)]
    resp_qs.extend(map(get_response_string, qs[:MAX_QUESTIONS]))

    if len(resp_qs) is 1:
        resp_qs.append(('No questions found. Please try a broader search or '
                        'search directly on '
                        '<https://stackoverflow.com|StackOverflow>.'))

    slack.notify(text='\n'.join(resp_qs), channel=channel())

    return Response('',
                    content_type='text/plain; charset=utf-8')


@app.route('/')
def hello():
    return Response(
        'A programmer\'s best friend, now in Slack. http://so.goel.io',
        content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
