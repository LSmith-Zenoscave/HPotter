"""Hpotter request/response logging schema ORM
"""
from enum import Enum

from sqlalchemy import Column, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy_utils import IPAddressType

# https://www.ietf.org/rfc/rfc1700.txt
TCP = 6
UDP = 17

BASE = declarative_base()


class Connections(BASE):
    """Describes a connection to a logged socket.
    """
    # pylint: disable=E0213, R0903
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    sourceIP = Column(IPAddressType)
    sourcePort = Column(Integer)
    destIP = Column(IPAddressType)
    destPort = Column(Integer)
    proto = Column(Integer)


class Credentials(BASE):
    """Describes connection credentials used to gain access.
    """
    # pylint: disable=E0213, R0903
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    username = Column(Text)
    password = Column(Text)
    connections_id = Column(Integer, ForeignKey('connections.id'))
    connection = relationship('Connections')


class Data(BASE):
    """Describes socket traffic data during the session.
    """
    # pylint: disable=E0213, R0903
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    kind = Enum('request', 'response')
    data = Column(Text)
    connections_id = Column(Integer, ForeignKey('connections.id'))
    connection = relationship('Connections')
