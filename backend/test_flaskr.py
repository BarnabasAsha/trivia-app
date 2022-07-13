import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from app import app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        # credentials is username and password
        self.credentials = "postgres:root"
        self.host = "localhost:5432"
        self.database_path = "postgresql://{}@{}/{}".format(
            self.credentials, self.host, self.database_name
        )
        setup_db(self.app, self.database_path)

        self.new_question = {
            "question": "Who was the first man on the moon?",
            "category": 1,
            "answer": "Niel Armstrong",
            "difficulty": 1,
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    ## Test cases
    def test_get_categories_success(self):
        res = self.client().get("/api/v1/categories")
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_questions(self):
        res = self.client().get("/api/v1/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["categories"]))

    def test_get_paginated_questions_not_found(self):
        res = self.client().get("/api/v1/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["error"], 404)

    def test_add_new_question_success(self):
        res = self.client().post("/api/v1/questions", json=self.new_question)
        data = json.loads(res.data)
        question = Question.query.get(data["added"])

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertTrue(question)

    def test_add_new_question_bad_request(self):
        res = self.client().post("/api/v1/questions", json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["error"], 400)

    def test_delete_question_success(self):
        question = Question(
            question=self.new_question["question"],
            answer=self.new_question["answer"],
            difficulty=self.new_question["difficulty"],
            category=self.new_question["category"],
        )
        question.insert()
        question_id = question.id

        res = self.client().delete("/api/v1/questions/" + str(question_id))
        data = json.loads(res.data)

        question = Question.query.get(question_id)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIsNone(question)

    def test_delete_question_not_found(self):
        res = self.client().delete("/api/v1/questions/1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["error"], 404)

    def test_search_questions_success(self):
        res = self.client().post("/api/v1/questions", json={"searchTerm": "movie"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["totalQuestions"])

    def test_search_questions_empty(self):
        res = self.client().post("/api/v1/questions", json={"searchTerm": ""})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["totalQuestions"])

    def test_search_questions_not_found(self):
        res = self.client().post("/api/v1/questions", json={"searchTerm": "xyzjklmnq"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertFalse(len(data["questions"]))
        self.assertFalse(data["totalQuestions"])

    def test_get_questions_in_category_success(self):
        res = self.client().get("/api/v1/categories/2/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["totalQuestions"])

    def test_get_question_for_quiz_success(self):
        res = self.client().post(
            "/api/v1/quizzes",
            json={"previous_questions": [], "quiz_category": {"type": "", "id": 4}},
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["question"])

    # def test_get_question_for_quiz_end_of_questions(self):
    #     res = self.client().post(
    #         "/api/v1/quizzes",
    #         json={
    #             "previous_questions": [10, 11],
    #             "quiz_category": {"type": "", "id": 5},
    #         },
    #     )
    #     data = json.loads(res.data)

    #     self.assertEqual(res.status_code, 200)
    #     self.assertFalse(data["question"])

    def test_get_question_for_quiz_bad_request(self):
        res = self.client().post("/api/v1/quizzes", json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["error"], 400)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
