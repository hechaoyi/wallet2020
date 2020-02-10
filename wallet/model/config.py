from time import time

from flask.json import dumps, loads

from wallet.core import db

TRANSACTION_TEMPLATES = 'transaction_templates'


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(32), nullable=False)
    val = db.Column(db.String(4096), nullable=False)
    # relationships
    user = db.relationship('User')
    # metadata
    __table_args__ = (
        db.UniqueConstraint('user_id', 'key', name='config_user_key_key'),
    )

    def __repr__(self):
        return f'<Config {self.key}>'

    @classmethod
    def _get(cls, user, key):
        return cls.query.filter_by(user=user, key=key).first()

    @classmethod
    def add_transaction_template(cls, user, template):
        template = {**loads(template), 'id': int(time())}
        config = cls._get(user, TRANSACTION_TEMPLATES)
        if config:
            config.val = dumps([*loads(config.val), template])
        else:
            db.save(cls(user=user, key=TRANSACTION_TEMPLATES, val=dumps([template])))
        return template['id']

    @classmethod
    def del_transaction_template(cls, user, template_id):
        config = cls._get(user, TRANSACTION_TEMPLATES)
        if config:
            config.val = dumps([template
                                for template in loads(config.val)
                                if template['id'] != int(template_id)])

    @classmethod
    def get_transaction_templates(cls, user):
        config = cls._get(user, TRANSACTION_TEMPLATES)
        return config.val if config else '[]'
