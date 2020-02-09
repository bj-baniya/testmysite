from . import opentdb as api
from random import shuffle
import json
import psycopg2
from collections import Counter

class PostgreHelp:
    def __init__(self):
        #self.redisClient = redis.Redis(host="127.0.0.1", port=6379)
        self.user = 'user'

        self.connection = psycopg2.connect(user="postgres",
                                           password="admin",
                                           host="127.0.0.1",
                                           port="5432",
                                           database="trivia")

        '''
        self.connection = psycopg2.connect(user="mmeqtzuigcrudl",
                                  password="2f55bd846a95842e210cc3ac1585d2254479ccd33219fc5615b23aa1de07feb9",
                                  host="ec2-184-72-236-57.compute-1.amazonaws.com",
                                  port="5432",
                                  database="dauao6n2jna0eu")  
        '''

    def SetQuestion(self, groupname):
        question = ''
        answers = ''
        try:

            cursor = self.connection.cursor()
            existingQuestion = "SELECT *  FROM public.questions where groupname = '{}' ".format(
                groupname)
            cursor.execute(existingQuestion)
            self.connection.commit()

            difficulty = 'easy'
            quesno = 0
            exist = False
            if cursor.rowcount > 0:
                row = cursor.fetchone()
                quesno = int(row[7])
                exist = True
            if quesno <= 10:
                difficulty = 'easy'
            elif quesno > 10 and quesno < 20:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            questionResult = api.GetQuestion(difficulty)
            result = questionResult['results'][0]
            question = result['question']
            correct_answer = result['correct_answer']
            answers = result['incorrect_answers']
            answers.append(correct_answer)
            shuffle(answers)
            quesno += 1
            if exist:

                #updateUserNO = "UPDATE questions SET  quesno=%s, correctanswer=%s, difficulty=%s, question=%s, answers=%s WHERE groupname= %s"
                #updateUserNO = (quesno,correct_answer,difficulty,question,answers,groupname)
                updateQuestionNo = "UPDATE questions SET  quesno=%s, correctanswer=%s, difficulty=%s, question=%s, answers=%s WHERE groupname= %s"
                ans = (quesno, correct_answer, difficulty,
                       question, '{}', groupname)
                cursor.execute(updateQuestionNo, ans)
                self.connection.commit()
            else:
                question_insert = "INSERT INTO public.questions(groupname, userno, correctanswer, difficulty, question,quesno) VALUES ( '{}',{},'{}','{}','{}',{})"
                question_insert = question_insert.format(
                    groupname, quesno, correct_answer, difficulty, question, 1)
                cursor.execute(question_insert)
                self.connection.commit()

        except (Exception, psycopg2.Error) as error:
            if(self.connection):
                print(error)
        finally:
            # closing database connection.
            if(self.connection):
                cursor.close()
                self.connection.close()
                print("PostgreSQL connection is closed")
        return (question, answers)

    def GetQuestion(self, groupname):
        cursor = self.connection.cursor()
        existingQuestion = 'SELECT * FROM public.questions where groupname = %s '
        cursor.execute(existingQuestion, groupname)
        self.connection.commit()
        question = None
        answers = None
        if cursor.rowcount > 0:
            row = cursor.fetchone()
            question = int(row[5])
            answers = int(row[6])
        return (question, answers)

    def GetUserCount(self, groupname, maxuser, username):
        # the group already contains the user
        cursor = self.connection.cursor()
        existing_user = "SELECT Count(1) FROM public.answers where groupname = '{0}' ".format(
            groupname)
        cursor.execute(existing_user)
        self.connection.commit()
        row = cursor.fetchone()
        totalusers = int(row[0])
        if(totalusers < maxuser):
            cursor = self.connection.cursor()
            existing_user = "SELECT Count(1) FROM public.answers where groupname = '{0}' and username= '{1}' ".format(
                groupname, username)
            cursor.execute(existing_user)
            self.connection.commit()
            row = cursor.fetchone()
            currentUser = int(row[0])
            if currentUser == 0:
                self.ConnectionAdd(groupname, username, '')
                totalusers += 1
        elif totalusers == maxuser:
            totalusers += 1
        return totalusers

    def UpdateUserCount(self, groupname, users):
        users += 1
        updateUserCount = "UPDATE questions SET  userno={0}  WHERE groupname= '{1}'".format(
            users, groupname)
        cursor = self.connection.cursor()
        cursor.execute(updateUserCount)
        self.connection.commit()
        return users

    def FirstUser(self, groupname, username):
        query_firstperson = "INSERT INTO public.questions(groupname, userno, correctanswer, difficulty, question,quesno) VALUES ( '{}',{},'{}','{}','{}',{})"
        query_firstperson = query_firstperson.format(
            groupname, 1, '', 'easy', '', 0)
        cursor = self.connection.cursor()
        cursor.execute(query_firstperson)
        self.connection.commit()
        self.ConnectionAdd(groupname, username, '')
        return 1

    def ConnectionAdd(self, groupname, username, ans):
        ans_query = "INSERT INTO public.answers( groupname, username, ans) VALUES ('{}', '{}', '{}')"
        ans_query = ans_query.format(groupname, username, ans)
        cursor = self.connection.cursor()
        cursor.execute(ans_query)
        self.connection.commit()

    def AnswerUpdate(self, groupname, username, ans):
        ans_query = "Update answers set ans = '{}' where groupname='{}' and  username='{}'"
        ans_query = ans_query.format(ans, groupname, username)
        cursor = self.connection.cursor()
        cursor.execute(ans_query)
        self.connection.commit()

    def GetCorrectAnswer(self, groupname):
        cursor = self.connection.cursor()
        existingQuestion = "SELECT correctanswer FROM public.questions where groupname = '{}'".format(groupname)
        cursor.execute(existingQuestion)
        self.connection.commit()
        answers = None
        if cursor.rowcount > 0:
            row = cursor.fetchone()
            answers = row[0]
        return answers

    def GetGroupAnswer(self, groupname):
        correct_answer = self.GetCorrectAnswer(groupname)
        cursor = self.connection.cursor()
        existingQuestion = "SELECT * FROM answers where groupname = '{}'".format(
            groupname)
        cursor.execute(existingQuestion)
        self.connection.commit()
        ans_result = []
        if cursor.rowcount > 0:
            rows = cursor.fetchall()
            for row in rows:
                answers = row[3]
                ans_result.append(answers)
        ans_stat = Counter(ans_result)
        print(ans_stat)
        return  (ans_stat.items(), correct_answer)