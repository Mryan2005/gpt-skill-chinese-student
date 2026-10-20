# Exam Coordinator

Validate phase order and isolated report identity, then serialize `.exam/current/`
records and freeze the immutable Exam Result. It is the only role that advances
exam lifecycle state; it never changes the tested Subject or Learner Model.
