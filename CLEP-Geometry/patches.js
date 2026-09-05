(function () {
  const bank = window.GEOMETRY_QUESTIONS || [];
  const q30 = bank.find(q => q.id === "G30");
  if (q30) {
    Object.assign(q30, {
      topic: "Quadrilaterals",
      level: "Layered",
      stem: "An isosceles trapezoid has bases of lengths 10 and 26 and legs of length 17. What is the area of the trapezoid?",
      choices: ["180", "240", "270", "306"],
      answer: 2,
      explanation: "Because the trapezoid is isosceles, the difference of the bases, 26 − 10 = 16, is split equally between the two sides. Each horizontal offset is 8. Using a right triangle with hypotenuse 17 gives the height √(17² − 8²) = 15. Therefore the area is (1/2)(10 + 26)(15) = 270.",
      diagram: { type: "isoscelesTrapezoidDerived", top: "10", bottom: "26", leg: "17", height: "?" }
    });
  }

  // Invalidate only pre-fix saved attempts once, so changed question/diagram state does not carry over.
  try {
    const migrationKey = "clep-geometry-diagram-fix-v2";
    if (!localStorage.getItem(migrationKey)) {
      localStorage.removeItem("clep-geometry-mastery-v1");
      localStorage.setItem(migrationKey, "1");
    }
  } catch (_) {}
})();