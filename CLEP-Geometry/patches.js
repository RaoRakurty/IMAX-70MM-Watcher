(function () {
  const bank = window.GEOMETRY_QUESTIONS || [];

  const q01 = bank.find(q => q.id === "G01");
  if (q01) {
    Object.assign(q01, {
      stem: "In isosceles triangle ABC, AB = AC = 25 and BC = 14. Point X is the midpoint of BC, and segment AX is drawn. What is the area of triangle ABC?",
      explanation: "Because the triangle is isosceles and X is the midpoint of the base, median AX is also an altitude. Thus BX = 7. From right triangle ABX, AX = √(25²−7²) = 24. Area = (1/2)(14)(24) = 168."
    });
  }

  const q30 = bank.find(q => q.id === "G30");
  if (q30) {
    Object.assign(q30, {
      topic: "Quadrilaterals",
      level: "Layered",
      stem: "An isosceles trapezoid has bases of lengths 10 and 26 and legs of length 17. What is the area of the trapezoid?",
      choices: ["180", "240", "270", "306"],
      answer: 2,
      explanation: "Because the trapezoid is isosceles, the difference of the bases, 26 − 10 = 16, is split equally between the two sides. Each horizontal offset is 8. Using a right triangle with hypotenuse 17 gives the height √(17² − 8²) = 15. Therefore the area is (1/2)(10 + 26)(15) = 270.",
      diagram: { type: "trapezoid", b1: "10", b2: "26", h: "?" }
    });
  }

  try {
    const migrationKey = "clep-geometry-diagram-fix-v3";
    if (!localStorage.getItem(migrationKey)) {
      localStorage.removeItem("clep-geometry-mastery-v1");
      localStorage.setItem(migrationKey, "1");
    }
  } catch (_) {}
})();