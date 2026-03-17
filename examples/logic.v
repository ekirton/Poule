Lemma modus_ponens : forall P Q : Prop, P -> (P -> Q) -> Q.
Proof.
  intros P Q Hp Hpq.
  apply Hpq.
  exact Hp.
Qed.

Lemma and_comm : forall P Q : Prop, P /\ Q -> Q /\ P.
Proof.
  intros P Q [Hp Hq].
  split.
  - exact Hq.
  - exact Hp.
Qed.
