;; BNPL expert-system rules.
;; Hard rules produce one hard-decision. Soft rules produce evidence facts.

(deftemplate categorical-input
  (slot name (type SYMBOL))
  (slot value (type SYMBOL)))

(deftemplate numeric-input
  (slot name (type SYMBOL))
  (slot value (type NUMBER)))

(deftemplate context
  (slot evaluation-type
        (type SYMBOL)
        (allowed-symbols new-application limit-review)))

(deftemplate hard-decision
  (slot rule-id (type SYMBOL))
  (slot action
        (type SYMBOL)
        (allowed-symbols reject suspend))
  (slot reason (type STRING)))

(deftemplate evidence
  (slot rule-id (type SYMBOL))
  (slot cf (type FLOAT))
  (slot reason (type STRING)))

;; Evidence sufficiency is assessed only for new applications after CF.
;; The full positive CF maximum for a new applicant is 2.50.
(deftemplate evidence-coverage
  (slot ratio (type FLOAT)))

(deftemplate tier-cap
  (slot rule-id (type SYMBOL))
  (slot maximum-limit (type INTEGER))
  (slot reason (type STRING)))

(defrule EC-01-low-evidence-coverage
  (context (evaluation-type new-application))
  (evidence-coverage (ratio ?r&:(< ?r 0.70)))
  (not (hard-decision))
  =>
  (assert (tier-cap (rule-id EC-01) (maximum-limit 1000)
    (reason "Evidence coverage is below 70 percent; new-applicant limit is capped at CNY 1,000."))))

(defrule EC-02-medium-evidence-coverage
  (context (evaluation-type new-application))
  (evidence-coverage (ratio ?r&:(and (>= ?r 0.70) (< ?r 0.90))))
  (not (hard-decision))
  =>
  (assert (tier-cap (rule-id EC-02) (maximum-limit 5000)
    (reason "Evidence coverage is between 70 and 90 percent; new-applicant limit is capped at CNY 5,000."))))

(defrule EC-03-sufficient-evidence-coverage
  (context (evaluation-type new-application))
  (evidence-coverage (ratio ?r&:(>= ?r 0.90)))
  (not (hard-decision))
  =>
  (assert (tier-cap (rule-id EC-03) (maximum-limit 10000)
    (reason "Evidence coverage is at least 90 percent; no additional tier cap applies."))))

;; ---------------------------------------------------------------------------
;; Hard rules
;; ---------------------------------------------------------------------------

(defrule HR-01-new-identity-failed
  (declare (salience 100))
  (context (evaluation-type new-application))
  (categorical-input (name identity-verified) (value no))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-01)
    (action reject)
    (reason "Identity verification failed."))))

(defrule HR-01-existing-identity-failed
  (declare (salience 100))
  (context (evaluation-type limit-review))
  (categorical-input (name identity-verified) (value no))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-01)
    (action suspend)
    (reason "Identity verification failed."))))

(defrule HR-02-new-underage
  (declare (salience 100))
  (context (evaluation-type new-application))
  (numeric-input (name age) (value ?age&:(< ?age 18)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-02)
    (action reject)
    (reason "Applicant is under 18."))))

(defrule HR-02-existing-underage
  (declare (salience 100))
  (context (evaluation-type limit-review))
  (numeric-input (name age) (value ?age&:(< ?age 18)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-02)
    (action suspend)
    (reason "User is under 18."))))

(defrule HR-03-new-adverse-credit
  (declare (salience 95))
  (context (evaluation-type new-application))
  (numeric-input (name adverse-credit-incidents-6m) (value ?n&:(>= ?n 2)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-03)
    (action reject)
    (reason "Two or more adverse credit incidents occurred in the last six months."))))

(defrule HR-03-existing-adverse-credit
  (declare (salience 95))
  (context (evaluation-type limit-review))
  (numeric-input (name adverse-credit-incidents-6m) (value ?n&:(>= ?n 2)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-03)
    (action suspend)
    (reason "Two or more adverse credit incidents occurred in the last six months."))))

(defrule HR-05-new-low-external-score
  (declare (salience 95))
  (context (evaluation-type new-application))
  (numeric-input (name external-credit-score) (value ?score&:(<= ?score 450)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-05)
    (action reject)
    (reason "External credit score is 450 or below."))))

(defrule HR-05-existing-low-external-score
  (declare (salience 95))
  (context (evaluation-type limit-review))
  (numeric-input (name external-credit-score) (value ?score&:(<= ?score 450)))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-05)
    (action suspend)
    (reason "External credit score is 450 or below."))))

(defrule HR-04-new-abnormal-device
  (declare (salience 90))
  (context (evaluation-type new-application))
  (categorical-input (name device-stability) (value abnormal))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-04)
    (action reject)
    (reason "Device activity is abnormal."))))

(defrule HR-04-existing-abnormal-device
  (declare (salience 90))
  (context (evaluation-type limit-review))
  (categorical-input (name device-stability) (value abnormal))
  (not (hard-decision))
  =>
  (assert (hard-decision
    (rule-id HR-04)
    (action suspend)
    (reason "Abnormal device activity suspends BNPL."))))

;; ---------------------------------------------------------------------------
;; Basic-information soft rules
;; ---------------------------------------------------------------------------

(defrule SR-01-verified-credit-card
  (categorical-input (name identity-verified) (value yes))
  (categorical-input (name linked-card-type) (value credit))
  =>
  (assert (evidence (rule-id SR-01) (cf 0.45)
    (reason "Identity is verified and a credit card is linked."))))

(defrule SR-02-verified-debit-card
  (categorical-input (name identity-verified) (value yes))
  (categorical-input (name linked-card-type) (value debit))
  =>
  (assert (evidence (rule-id SR-02) (cf 0.25)
    (reason "Identity is verified and a debit card is linked."))))

(defrule SR-03-no-linked-card
  (categorical-input (name linked-card-type) (value none))
  =>
  (assert (evidence (rule-id SR-03) (cf -0.25)
    (reason "No payment card is linked."))))

(defrule SR-04-established-account
  (numeric-input (name account-age-months) (value ?m&:(>= ?m 12)))
  =>
  (assert (evidence (rule-id SR-04) (cf 0.35)
    (reason "The account has been registered for at least 12 months."))))

(defrule SR-05-growing-account
  (numeric-input (name account-age-months) (value ?m&:(and (>= ?m 6) (< ?m 12))))
  =>
  (assert (evidence (rule-id SR-05) (cf 0.20)
    (reason "The account has been registered for 6 to 11 months."))))

(defrule SR-06-very-new-account
  (numeric-input (name account-age-months) (value ?m&:(< ?m 1)))
  =>
  (assert (evidence (rule-id SR-06) (cf -0.20)
    (reason "The account is less than one month old."))))

;; ---------------------------------------------------------------------------
;; Platform-behaviour soft rules
;; ---------------------------------------------------------------------------

(defrule SR-07-excellent-fulfilment
  (context (evaluation-type limit-review))
  (numeric-input (name repayment-fulfilment-rate) (value ?r&:(>= ?r 0.98)))
  =>
  (assert (evidence (rule-id SR-07) (cf 0.65)
    (reason "Repayment fulfilment rate is at least 98 percent."))))

(defrule SR-08-good-fulfilment
  (context (evaluation-type limit-review))
  (numeric-input (name repayment-fulfilment-rate) (value ?r&:(and (>= ?r 0.95) (< ?r 0.98))))
  =>
  (assert (evidence (rule-id SR-08) (cf 0.40)
    (reason "Repayment fulfilment rate is between 95 and 98 percent."))))

(defrule SR-09-acceptable-fulfilment
  (context (evaluation-type limit-review))
  (numeric-input (name repayment-fulfilment-rate) (value ?r&:(and (>= ?r 0.90) (< ?r 0.95))))
  =>
  (assert (evidence (rule-id SR-09) (cf 0.15)
    (reason "Repayment fulfilment rate is between 90 and 95 percent."))))

(defrule SR-10-low-fulfilment
  (context (evaluation-type limit-review))
  (numeric-input (name repayment-fulfilment-rate) (value ?r&:(< ?r 0.90)))
  =>
  (assert (evidence (rule-id SR-10) (cf -0.50)
    (reason "Repayment fulfilment rate is below 90 percent."))))

(defrule SR-11-high-spending
  (numeric-input (name average-monthly-spending) (value ?v&:(>= ?v 2000)))
  =>
  (assert (evidence (rule-id SR-11) (cf 0.30)
    (reason "Average monthly spending is at least CNY 2,000."))))

(defrule SR-12-medium-spending
  (numeric-input (name average-monthly-spending) (value ?v&:(and (>= ?v 1000) (< ?v 2000))))
  =>
  (assert (evidence (rule-id SR-12) (cf 0.15)
    (reason "Average monthly spending is between CNY 1,000 and 2,000."))))

(defrule SR-13-many-completed-orders
  (numeric-input (name completed-order-count) (value ?n&:(>= ?n 100)))
  =>
  (assert (evidence (rule-id SR-13) (cf 0.30)
    (reason "At least 100 orders have been completed."))))

(defrule SR-14-some-completed-orders
  (numeric-input (name completed-order-count) (value ?n&:(and (>= ?n 50) (< ?n 100))))
  =>
  (assert (evidence (rule-id SR-14) (cf 0.15)
    (reason "Between 50 and 99 orders have been completed."))))

(defrule SR-15-long-on-time-streak
  (context (evaluation-type limit-review))
  (numeric-input (name consecutive-on-time-repayments) (value ?n&:(>= ?n 6)))
  =>
  (assert (evidence (rule-id SR-15) (cf 0.55)
    (reason "At least six consecutive repayments were made on time."))))

(defrule SR-16-short-on-time-streak
  (context (evaluation-type limit-review))
  (numeric-input (name consecutive-on-time-repayments) (value ?n&:(and (>= ?n 3) (< ?n 6))))
  =>
  (assert (evidence (rule-id SR-16) (cf 0.25)
    (reason "Three to five consecutive repayments were made on time."))))

(defrule SR-17-one-adverse-incident
  (numeric-input (name adverse-credit-incidents-6m) (value 1))
  =>
  (assert (evidence (rule-id SR-17) (cf -0.35)
    (reason "One adverse credit incident occurred in the last six months."))))

(defrule SR-18-stable-device
  (categorical-input (name device-stability) (value stable))
  =>
  (assert (evidence (rule-id SR-18) (cf 0.25)
    (reason "Device usage is stable."))))

(defrule SR-19-changing-device
  (categorical-input (name device-stability) (value changing))
  =>
  (assert (evidence (rule-id SR-19) (cf -0.15)
    (reason "Device usage has changed recently."))))

;; ---------------------------------------------------------------------------
;; External-credit soft rules
;; ---------------------------------------------------------------------------

(defrule SR-20-high-external-score
  (numeric-input (name external-credit-score) (value ?s&:(>= ?s 800)))
  =>
  (assert (evidence (rule-id SR-20) (cf 0.55)
    (reason "External credit score is at least 800."))))

(defrule SR-21-medium-external-score
  (numeric-input (name external-credit-score) (value ?s&:(and (>= ?s 550) (< ?s 800))))
  =>
  (assert (evidence (rule-id SR-21) (cf 0.30)
    (reason "External credit score is between 550 and 799."))))

(defrule SR-22-neutral-external-score
  (numeric-input (name external-credit-score) (value ?s&:(and (> ?s 450) (< ?s 550))))
  =>
  (assert (evidence (rule-id SR-22) (cf 0.0)
    (reason "External credit score is between 451 and 549."))))

(defrule SR-23-minor-external-overdue
  (categorical-input (name external-overdue-record) (value minor))
  =>
  (assert (evidence (rule-id SR-23) (cf -0.25)
    (reason "External overdue record is minor."))))

(defrule SR-24-moderate-external-overdue
  (categorical-input (name external-overdue-record) (value moderate))
  =>
  (assert (evidence (rule-id SR-24) (cf -0.55)
    (reason "External overdue record is moderate."))))

(defrule SR-25-serious-external-overdue
  (categorical-input (name external-overdue-record) (value serious))
  =>
  (assert (evidence (rule-id SR-25) (cf -0.70)
    (reason "External overdue record is serious."))))

(defrule SR-26-no-external-overdue
  (categorical-input (name external-overdue-record) (value none))
  =>
  (assert (evidence (rule-id SR-26) (cf 0.30)
    (reason "No external overdue record is present."))))

;; ---------------------------------------------------------------------------
;; Credit-limit utilisation soft rules
;; ---------------------------------------------------------------------------

(defrule SR-27-balanced-utilisation
  (context (evaluation-type limit-review))
  (numeric-input (name credit-limit-utilisation-rate)
    (value ?r&:(and (>= ?r 0.40) (<= ?r 0.80))))
  =>
  (assert (evidence (rule-id SR-27) (cf 0.30)
    (reason "Credit limit utilisation is between 40 and 80 percent."))))

(defrule SR-28-low-utilisation
  (context (evaluation-type limit-review))
  (numeric-input (name credit-limit-utilisation-rate) (value ?r&:(< ?r 0.20)))
  =>
  (assert (evidence (rule-id SR-28) (cf 0.0)
    (reason "Credit limit utilisation is below 20 percent."))))

(defrule SR-29-very-high-utilisation
  (context (evaluation-type limit-review))
  (numeric-input (name credit-limit-utilisation-rate) (value ?r&:(> ?r 0.90)))
  =>
  (assert (evidence (rule-id SR-29) (cf -0.30)
    (reason "Credit limit utilisation is above 90 percent."))))
