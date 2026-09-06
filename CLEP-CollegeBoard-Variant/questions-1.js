window.CLEP_QUESTIONS=window.CLEP_QUESTIONS||[];
window.CLEP_QUESTIONS.push(...[
  {
    "id": 1,
    "topic": "Financial Mathematics",
    "type": "mc",
    "stem": "Carl deposited P dollars into a savings account that earned 6 percent annual interest, compounded semiannually. Carl made no additional deposits to or withdrawals from the account. After two years, the account had a total value of $11,255.09. What was the value of P?",
    "choices": [
      {"text": "$9,400"},{"text": "$10,000"},{"text": "$10,600"},{"text": "$11,200"}
    ],
    "answer": 1,
    "explanation": "Use A = P(1 + r/n)^(nt). Here 11,255.09 = P(1.03)^4, so P is approximately $10,000."
  },
  {
    "id": 2,"topic": "Geometry","type": "mc",
    "stem": "Triangle DEF (not shown) is similar to triangle ABC shown, with angle B congruent to angle E and angle C congruent to angle F. The length of side DE is 12 cm. If the area of triangle ABC is 6 square centimeters, what is the area of triangle DEF?",
    "stimulus": {"kind":"svg","key":"similarTriangle"},
    "choices": [{"text":"24 cm²"},{"text":"48 cm²"},{"text":"72 cm²"},{"text":"96 cm²"}],
    "answer":3,
    "explanation":"AB = 3 cm corresponds to DE = 12 cm, so the linear scale factor is 4. Areas scale by 4² = 16, giving 6 × 16 = 96 cm²."
  },
  {
    "id":3,"topic":"Numbers","type":"matrix",
    "stem":"m is an odd integer. For each of the following numbers, indicate whether the number is odd or even.",
    "rows":["2m − 3","4m + 2","m² − m","m² + m + 1"],"columns":["Odd","Even"],"answer":[0,1,1,0],
    "explanation":"For odd m: 2m is even, so 2m−3 is odd; 4m+2 is even; m² and m are both odd so m²−m is even; m²+m+1 is odd+odd+1 = odd."
  },
  {
    "id":4,"topic":"Algebra & Functions","type":"numeric",
    "stem":"For any positive integers a and b, the operation ⊙ is defined as a ⊙ b = (3a − 2)^(b − 1). What is the value of (2 ⊙ 2) ⊙ 2?",
    "answer":10,"explanation":"First, 2 ⊙ 2 = (6−2)^1 = 4. Then 4 ⊙ 2 = (12−2)^1 = 10."
  },
  {
    "id":5,"topic":"Algebra & Functions","type":"mc",
    "stem":"A company manufactures precision components that each must weigh from 47.2 grams to 48.8 grams, inclusive. Which of the following inequalities describes all acceptable weights x, in grams, for each component?",
    "choices":[{"text":"|48 − x| ≤ 0.8"},{"text":"|48 − x| > 0.8"},{"text":"48 − x ≤ 0.8"},{"text":"48 − x > 0.8"}],
    "answer":0,"explanation":"The acceptable interval is centered at 48 with a maximum distance of 0.8, so |48−x| ≤ 0.8."
  },
  {
    "id":6,"topic":"Data Analysis & Statistics","type":"mc",
    "stem":"On a group trip, 15 people who were 18 years old, 15 people who were 24 years old, and 15 people who were 30 years old purchased tickets. One 24-year-old ticket holder became ill and did not go, while everyone else went. Which statement is true?",
    "choices":[{"text":"The standard deviation of the ages of the people who went is greater than the standard deviation of the ages of the people who purchased tickets."},{"text":"The standard deviation of the ages of the people who went is less than the standard deviation of the ages of the people who purchased tickets."},{"text":"The two standard deviations are equal."},{"text":"There is not enough information to determine which standard deviation is greater."}],
    "answer":0,"explanation":"The removed age, 24, is exactly at the mean. Removing a value at the mean leaves the same center but increases the average squared distance from the mean, so the standard deviation increases."
  },
  {
    "id":7,"topic":"Counting & Probability","type":"mc",
    "stem":"When Maya makes a sandwich, she may choose from among 4 kinds of bread, 5 varieties of filling, and 3 types of cheese. If she chooses one bread, one filling, and one type of cheese, how many different kinds of sandwiches can she make?",
    "choices":[{"text":"12"},{"text":"20"},{"text":"60"},{"text":"240"}],"answer":2,"explanation":"By the multiplication rule, 4 × 5 × 3 = 60."
  },
  {
    "id":8,"topic":"Algebra & Functions","type":"mc",
    "stem":"Which of the following subsets of the real numbers best describes the solution set of the inequality 4x − 12 ≤ 0?",
    "choices":[{"text":"(−∞, 3]"},{"text":"[3, ∞)"},{"text":"(−∞, ∞)"},{"text":"(−∞, −3] ∪ [4, ∞)"}],"answer":0,"explanation":"4x ≤ 12, so x ≤ 3."
  }
]);
