window.QUESTION_BANK = window.QUESTION_BANK || [];
window.QUESTION_BANK.push(
{
  "id": "L4","topic": "Logic & Sets","cognitive": "routine","type": "choice","stem": "Set A contains 58 elements and set B contains 44 elements. If 19 elements are in both A and B, how many elements are in A ∪ B?","choices": ["63","83","102","121"],"answer": 1,"explanation": "Use n(A∪B)=n(A)+n(B)-n(A∩B)=58+44-19=83.","stimulusHtml": ""
},
{
  "id": "L5","topic": "Logic & Sets","cognitive": "routine","type": "choice","stem": "Let A = {r, s, t} and B = {1, 2}. Which of the following ordered pairs is NOT in A × B?","choices": ["(r, 1)","(t, 2)","(s, 1)","(1, r)"],"answer": 3,"explanation": "In A × B, the first coordinate must be from A and the second from B. (1,r) reverses the order.","stimulusHtml": ""
},
{
  "id": "L6","topic": "Logic & Sets","cognitive": "routine","type": "choice","stem": "Which of the following is the negation of the statement 'Every application was approved'?","choices": ["No application was approved.","At least one application was not approved.","Every application was rejected.","At least one application was approved."],"answer": 1,"explanation": "The negation of 'every A has property P' is 'at least one A does not have property P.'","stimulusHtml": ""
},
{
  "id": "L7","topic": "Logic & Sets","cognitive": "nonroutine","type": "choice","stem": "A student asserted that x² + 1 is greater than 2x for every real number x. Which of the following values of x provides a counterexample to the student's claim?","choices": ["-1","0","1","2"],"answer": 2,"explanation": "At x=1, x²+1=2 and 2x=2, so the strict inequality is false.","stimulusHtml": ""
},
{
  "id": "L8","topic": "Logic & Sets","cognitive": "routine","type": "choice","stem": "Let R = {x | x > -2} and S = {x | x ≤ 3}. How many integers are in R ∩ S?","choices": ["4","5","6","7"],"answer": 1,"explanation": "The integers satisfying -2 < x ≤ 3 are -1, 0, 1, 2, and 3: five integers.","stimulusHtml": ""
},
{
  "id": "L9","topic": "Logic & Sets","cognitive": "routine","type": "choice","stem": "Which of the following is logically equivalent to the statement 'It is not true that both P and Q are true'?","choices": ["not P and not Q","not P or not Q","P or Q","P and not Q"],"answer": 1,"explanation": "By De Morgan's law, not(P and Q) is equivalent to (not P) or (not Q).","stimulusHtml": ""
},
{
  "id": "P1","topic": "Counting & Probability","cognitive": "routine","type": "choice","stem": "A cafeteria offers 4 entrees, 3 side dishes, 2 desserts, and 2 drinks. If a meal consists of one item from each category, how many different meals are possible?","choices": ["11","24","48","96"],"answer": 2,"explanation": "Use the multiplication principle: 4·3·2·2 = 48.","stimulusHtml": ""
},
{
  "id": "P2","topic": "Counting & Probability","cognitive": "nonroutine","type": "choice","stem": "A committee is to consist of 2 faculty members chosen from 7 faculty members and 3 students chosen from 9 students. How many different committees can be formed?","choices": ["252","756","1,764","3,024"],"answer": 2,"explanation": "Choose independently: C(7,2)·C(9,3)=21·84=1,764.","stimulusHtml": ""
},
{
  "id": "P3","topic": "Counting & Probability","cognitive": "routine","type": "choice","stem": "Seven finalists are available for the positions of president, vice president, and secretary. No person may hold more than one position. How many different assignments of the three positions are possible?","choices": ["35","105","210","343"],"answer": 2,"explanation": "Order matters: 7 choices for president, then 6, then 5. Thus 7·6·5=210.","stimulusHtml": ""
},
{
  "id": "P4","topic": "Counting & Probability","cognitive": "nonroutine","type": "choice","stem": "A fair six-sided die is rolled twice. What is the probability that the first roll is a multiple of 3 or the second roll is 5?","choices": ["1/3","4/9","1/2","5/9"],"answer": 1,"explanation": "P(first multiple of 3)=2/6=1/3. P(second is 5)=1/6. Subtract overlap 1/18: 1/3+1/6-1/18=4/9.","stimulusHtml": ""
},
{
  "id": "P5","topic": "Counting & Probability","cognitive": "routine","type": "choice","stem": "In a large group of employees, 40 percent are at least 30 years old and 30 percent hold a certain certification. Age and certification status are independent. What is the probability that a randomly selected employee is at least 30 years old and holds the certification?","choices": ["0.12","0.28","0.58","0.70"],"answer": 0,"explanation": "For independent events, multiply: 0.40·0.30=0.12.","stimulusHtml": ""
},
{
  "id": "P6","topic": "Counting & Probability","cognitive": "nonroutine","type": "choice","stem": "A box contains 9 white cards and 6 black cards. One card is selected at random and not replaced. If the first card selected was white, what is the probability that the second card selected will be black?","choices": ["2/5","3/7","6/15","9/14"],"answer": 1,"explanation": "After a white card is removed, 14 cards remain, including all 6 black cards. The probability is 6/14=3/7.","stimulusHtml": ""
}
);
