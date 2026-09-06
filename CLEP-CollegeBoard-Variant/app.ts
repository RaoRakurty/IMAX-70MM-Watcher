export type Topic="Algebra & Functions"|"Counting & Probability"|"Data Analysis & Statistics"|"Financial Mathematics"|"Geometry"|"Logic & Sets"|"Numbers";
export type AnswerValue=number|number[]|string;
export interface Choice{text:string;diagramKey?:string}
export interface BaseQuestion{id:number;topic:Topic;stem:string;explanation:string;stimulus?:{kind:"svg";key:string}|{kind:"html";html:string}}
export interface MCQuestion extends BaseQuestion{type:"mc";choices:Choice[];answer:number}
export interface NumericQuestion extends BaseQuestion{type:"numeric";answer:number;tolerance?:number;suffix?:string}
export interface MatrixQuestion extends BaseQuestion{type:"matrix";rows:string[];columns:string[];answer:number[]}
export type Question=MCQuestion|NumericQuestion|MatrixQuestion;
export interface SavedResult{id:string;startedAt:number;submittedAt:number;score:number;total:number;answers:Record<string,AnswerValue>}
// Browser-ready JavaScript is split into core.js, exam.js, results.js and the question-bank files for GitHub Pages.
