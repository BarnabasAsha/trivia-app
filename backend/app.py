import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# create and configure the app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
setup_db(app)


def paginate(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    data = [item.format() for item in selection]
    current_data = data[start:end]

    return current_data


@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization")
    response.headers.add(
        "Access-Control-Allow-Headers", "GET, POST, PATCH, DELETE, OPTIONS"
    )
    return response


@app.route("/api/v1")
def welcome():
    return jsonify({"success": True, "message": "Welcome to Trivia V1 API"})


# fetch categories endpoint


@app.route("/api/v1/categories")
def get_categories():
    categories = Category.query.all()
    formatted_categories = {
        category.id: category.type for category in categories}

    return jsonify({"categories": formatted_categories})


# fetch paginated questions endpoint


@app.route("/api/v1/questions")
def get_questions():
    questions = Question.query.order_by(Question.id).all()
    categories = Category.query.order_by(Category.id).all()
    current_questions = paginate(request, questions)
    if len(current_questions) == 0:
        abort(404)

    return jsonify({"success": True,
                    "questions": current_questions,
                    "categories": {category.id: category.type for category in categories},
                    "current_category": None,
                    "total_questions": len(Question.query.all()),
                    })


# Delete question endpoint using question id


@app.route("/api/v1/questions/<int:question_id>", methods=["DELETE"])
def delete_question(question_id):
    question = Question.query.filter(Question.id == question_id).one_or_none()

    if question is None:
        abort(404)
    try:
        question.delete()

        return jsonify(
            {
                "success": True,
                "deleted": question_id,
            }
        )
    except BaseException:
        abort(422)


# Create a new Question endpoint


@app.route("/api/v1/questions", methods=["POST"])
def add_question():
    try:
        data = request.get_json()

        searchTerm = data.get("searchTerm", None)

        if searchTerm is not None:
            questions = Question.query.filter(
                Question.question.ilike("%{}%".format(searchTerm))
            ).all()
            formatted_questions = [question.format() for question in questions]

            return jsonify(
                {
                    "questions": formatted_questions,
                    "totalQuestions": len(questions),
                    "currentCategory": None,
                }
            )
        else:
            question = data["question"]
            answer = data["answer"]
            difficulty = int(data["difficulty"])
            category = int(data["category"])

            question = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category,
            )

            question.insert()

            return jsonify({"added": question.id, "success": True})

    except Exception:
        abort(400)


# Get questions based on category
@app.route("/api/v1/categories/<int:category_id>/questions")
def get_questions_in_category(category_id):

    questions = Question.query.filter_by(category=category_id).all()
    formatted_questions = [question.format() for question in questions]

    return jsonify(
        {
            "questions": formatted_questions,
            "totalQuestions": len(questions),
            "currentCategory": None,
        }
    )


# quiz endpoint


@app.route("/api/v1/quizzes", methods=["POST"])
def get_question_for_quiz():

    data = request.get_json()
    try:
        previous_questions = data["previous_questions"]
        quiz_category = data["quiz_category"]["id"]
    except Exception:
        abort(400)

    if quiz_category:
        questions = (
            Question.query.filter_by(category=quiz_category)
            .filter(Question.id.notin_(previous_questions))
            .all()
        )
    else:
        questions = Question.query.filter(
            ~Question.category.in_(previous_questions)
        ).all()

    question = random.choice(questions).format() if questions else None

    return jsonify({"question": question})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": 404,
                   "message": "Not found"}), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400,
                   "message": "Bad Request"}), 400


@app.errorhandler(405)
def not_allowed(error):
    return (jsonify({"success": False, "error": 405,
                     "message": "Method not allowed"}), 405, )


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"success": False, "error": 422,
                   "message": "Unprocessable"}), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": 500, "message": "Internal server error."})


# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run(debug=True)

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
