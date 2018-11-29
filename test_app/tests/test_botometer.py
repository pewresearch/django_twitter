from django.test import TransactionTestCase
from django.conf import settings
from django.apps import apps
from django.core.management import call_command

import csv


class TestBotometer(TransactionTestCase):

    def test_default(self):
        call_command("django_twitter_get_user_followers", "g3hbee")
        user_model = apps.get_model(app_label=settings.TWITTER_APP,
                                    model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        print("Calculating botometer scores...")
        count = 0
        for user in user_model:
            count += 1
            call_command("django_twitter_get_user_botometer_score", user,
                         botometer_key="UjEfOgEaNVmsht9y9cXjHYYQFmpPp1Dpk6ojsnPxPEwluSQFMp")
            print(count)

        self.push_assert(len(user_model))

    def test_keyword(self):
        call_command("django_twitter_collect_tweet_stream", keyword="Putin", limit="5 min")

        tweets = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL).objects.all()
        count = 0
        for tweet in tweets:
            call_command("django_twitter_get_user_botometer_score", tweet.profile.twitter_id,
                         botometer_key="UjEfOgEaNVmsht9y9cXjHYYQFmpPp1Dpk6ojsnPxPEwluSQFMp")
            count += 1
            print(count)

        user_model = apps.get_model(app_label=settings.TWITTER_APP,
                                    model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        print("Total tweets: " + str(len(tweets)))
        print(len(user_model))
        self.push_assert(len(user_model))

    def test_stream(self):
        call_command("django_twitter_collect_tweet_stream", limit="50 tweets", queue_size=10)

        tweets = apps.get_model(app_label=settings.TWITTER_APP, model_name=settings.TWEET_MODEL).objects.all()
        print("Total tweets: " + str(len(tweets)))

        # user_model = apps.get_model(app_label=settings.TWITTER_APP,
        #                             model_name=settings.TWITTER_PROFILE_MODEL).objects.all()
        # print("Total users: " + str(len(user_model)))
        #
        # for tweet in tweets:
        #     print("{}: {}". format(tweet.id, tweet.profile.twitter_id))
        #     for user in user_model:
        #         if user.twitter_id in str(tweet.json):
        #             print(user.twitter_id)

        id_list = []
        for tweet in tweets:
            if tweet.profile.twitter_id not in id_list:
                id_list.append(str(tweet.profile.twitter_id))

        call_command("django_twitter_get_users_botometer_scores", twitter_ids=id_list, num_cores=8,
                     botometer_key="UjEfOgEaNVmsht9y9cXjHYYQFmpPp1Dpk6ojsnPxPEwluSQFMp")

        self.push_assert(len(tweets))

    def push_assert(self, length):

        # indexed as 0:0-0.2, 1:0.2-0.4, 2: 0.4-0.6, 3: 0.6-0.8, 4: 0.8-0.9, 5: 0.9-0.95, 6: 0.95-1
        cap_score = [0, 0, 0, 0, 0, 0, 0]
        # indexed as 0: 0-1, 1:1-2, 2:2-3, 3:3-4, 4:4-4.5, 5:4.5-5
        display_score = [0, 0, 0, 0, 0, 0]
        errorCount = 0
        botometer_model = apps.get_model(app_label=settings.TWITTER_APP,
                                         model_name=settings.BOTOMETER_SCORE_MODEL).objects.all()

        # self.assertEqual(length, len(botometer_model))

        for score in botometer_model:
            if "error" not in score.json:
                self.assertIsNotNone(score.json["display_scores"]["english"])
                self.assertIsNotNone(score.json["cap"]["english"])

                if 0 <= score.json["display_scores"]["english"] <= 1:
                    display_score[0] += 1
                elif 1 < score.json["display_scores"]["english"] <= 2:
                    display_score[1] += 1
                elif 2 < score.json["display_scores"]["english"] <= 3:
                    display_score[2] += 1
                elif 3 < score.json["display_scores"]["english"] <= 4:
                    display_score[3] += 1
                elif 4 < score.json["display_scores"]["english"] <= 4.5:
                    display_score[4] += 1
                elif 4.5 < score.json["display_scores"]["english"] <= 5:
                    display_score[5] += 1

                if 0 <= score.json["cap"]["english"] <= 0.2:
                    cap_score[0] += 1
                elif 0.2 < score.json["cap"]["english"] <= 0.4:
                    cap_score[1] += 1
                elif 0.4 < score.json["cap"]["english"] <= 0.6:
                    cap_score[2] += 1
                elif 0.6 < score.json["cap"]["english"] <= 0.8:
                    cap_score[3] += 1
                elif 0.8 < score.json["cap"]["english"] <= 0.9:
                    cap_score[4] += 1
                elif 0.9 < score.json["cap"]["english"] <= 0.95:
                    cap_score[5] += 1
                elif 0.95 < score.json["cap"]["english"] <= 1:
                    cap_score[6] += 1
            else:
                errorCount += 1

        wr = open("capscores.csv", 'wb')
        wr.write("0-0.2,0.2-0.4,0.4-0.6,0.6-0.8,0.8-0.9,0.9-0.95,0.95-1,errors,total\n")
        total = 0
        for i in cap_score:
            wr.write(str(i))
            total += i
            wr.write(",")
        wr.write(str(errorCount))
        wr.write(",")
        total += errorCount
        wr.write(str(total))
        wr.close()

        total = 0
        wr = open("displayscores.csv", 'wb')
        wr.write("0-1,1-2,2-3,3-4,4-4.5,4.5-5,errors,total\n")
        for i in display_score:
            wr.write(str(i))
            total += i
            wr.write(",")
        wr.write(str(errorCount))
        wr.write(",")
        total += errorCount
        wr.write(str(total))
        wr.close()
