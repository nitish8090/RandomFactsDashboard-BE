import os
import csv
import random
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reset_code = db.Column(db.String(120))
    facts = db.relationship("Facts", cascade="all,delete")
    is_admin = db.Column(db.Boolean, default=False)

    # Extra information
    address = db.Column(db.Text())
    post_code = db.Column(db.Text())
    landmark = db.Column(db.Text())
    education = db.Column(db.Text())
    country = db.Column(db.Text())
    state = db.Column(db.Text())

    def generate_starting_facts(self):
        with open(os.path.join(Path(__file__).parent.parent, "random_facts.csv")) as csvfile:
            random_facts = [_[0] for _ in csv.reader(csvfile)]

            # Select 3 facts from the list at random
            db.session.add_all([Facts(user=self.id, fact_text=_) for _ in random.sample(random_facts, 3)])

        db.session.commit()

    def serialize(self, include_password=False, include_facts=False, include_is_admin=False):
        return_dict = {_: getattr(self, _) for _ in
                       ('id', 'name', 'email', 'address', 'post_code', 'landmark', 'education', 'country', 'state')}
        if include_password:
            return_dict['password'] = self.password
        if include_facts:
            return_dict['facts'] = [{"id": f.id, "fact_text": f.fact_text} for f in self.facts]
        if include_is_admin:
            return_dict['is_admin'] = self.is_admin
        return return_dict


class Facts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    fact_text = db.Column(db.Text())

    def serialize(self):
        return {"id": self.id, "fact_text": self.fact_text}
