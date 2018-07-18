from django.test import TransactionTestCase
from django.conf import settings
from django.apps import apps
from django.core.management import call_command

import csv


class TestBotometer(TransactionTestCase):
    def setUp(self):
        call_command("django_twitter_get_user_followers", "pankhurikumar23")

    def test_default(self):
        user_model = apps.get_model(app_label=settings.TWITTER_APP,
                                    model_name=settings.TWITTER_PROFILE_MODEL).objects.all()

        count = 0
        idx = 0
        # indexed as 0:0-0.2, 1:0.2-0.4, 2: 0.4-0.6, 3: 0.6-0.8, 4: 0.8-0.9, 5: 0.9-0.95, 6: 0.95-1
        cap_score = [0, 0, 0, 0, 0, 0, 0]
        # indexed as 0: 0-1, 1:1-2, 2:2-3, 3:3-4, 4:4-4.5, 5:4.5-5
        display_score = [0, 0, 0, 0, 0, 0]
        errorCount = 0
        for user in user_model:
            call_command("django_twitter_get_user_botometer_score", user,
                         botometer_key="UjEfOgEaNVmsht9y9cXjHYYQFmpPp1Dpk6ojsnPxPEwluSQFMp")
            if (count + 1) % 20 == 0:
                print("Saving newly added scores...")
                botometer_model = apps.get_model(app_label=settings.TWITTER_APP,
                                                 model_name=settings.BOTOMETER_SCORE_MODEL).objects.all()
                curr = 0
                while curr < 20:
                    score = botometer_model[idx + curr]
                    if "error" not in score.json:
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
                    curr += 1
                idx += curr + 1

                print("Errors: " + str(errorCount))
                print("Cap: ")
                print("0.0-0.2: " + str(cap_score[0]))
                print("0.2-0.4: " + str(cap_score[1]))
                print("0.4-0.6: " + str(cap_score[2]))
                print("0.6-0.8: " + str(cap_score[3]))
                print("0.8-0.9: " + str(cap_score[4]))
                print("0.9-0.95: " + str(cap_score[5]))
                print("0.95-1: " + str(cap_score[6]))
                print("Display: ")
                print("0-1: " + str(display_score[0]))
                print("1-2: " + str(display_score[1]))
                print("2-3: " + str(display_score[2]))
                print("3-4: " + str(display_score[3]))
                print("4-4.5: " + str(display_score[4]))
                print("4.5-5: " + str(display_score[5]))

            count += 1
            print(count)

        botometer_model = apps.get_model(app_label=settings.TWITTER_APP,
                                         model_name=settings.BOTOMETER_SCORE_MODEL).objects.all()

        # self.assertEqual(len(user_model), len(botometer_model))

        count = 0
        for score in botometer_model:
            if "error" not in score.json:
                count += 1
                # print(count)
                self.assertIsNotNone(score.json["display_scores"]["english"])
                self.assertIsNotNone(score.json["cap"]["english"])
            else:
                print(score.json)

        for score in botometer_model:
            if "error" not in score.json:
                print(score.json)
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

        print("Errors: " + str(errorCount))
        with open('capscores.csv', 'wb') as myFile:
            wr = csv.writer(myFile, quoting=csv.QUOTE_ALL)
            wr.writerow(cap_score)

        with open('displayscores.csv', 'wb') as myFile:
            wr = csv.writer(myFile, quoting=csv.QUOTE_ALL)
            wr.writerow(display_score)
