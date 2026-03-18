From Coq Require Import List.
Import ListNotations.

Lemma app_nil_r : forall (A : Type) (l : list A), l ++ [] = l.
Proof.
  intros A l.
  induction l as [| a l' IH].
  - reflexivity.
  - simpl. rewrite IH. reflexivity.
Qed.

Lemma rev_involutive : forall (A : Type) (l : list A), rev (rev l) = l.
Proof.
  intros A l.
  induction l as [| a l' IH].
  - reflexivity.
  - simpl. rewrite rev_app_distr. simpl. rewrite IH. reflexivity.
Qed.
