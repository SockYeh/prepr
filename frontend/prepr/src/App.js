import React, {useState, useEffect} from "react";
import api from './api';
import COLORS from "./constants";

const table_style = {
    "background-color": COLORS.background,
    "color": COLORS.text,
    "border-collapse": "collapse",
    "width": "80%",
    "text-align": "left",
    "margin": "auto",
    "margin-top": "10%"
}

const td_th_style = {
    "height": "5vh"
}

function get_colored_string(string) {
    if (string === "Hard") {
        return {"color": "#f53333"}
    } else if (string === "Medium") {
        return {"color": "#f5c431"}
    } else {
        return {"color": "#3bf538"}
    }
}

function crop(string) {
    return string.slice(0, 40) + (string.length > 45 ? '...' : '')
}

const App = () => {
    // const [problems, setProblems] = useState([]);

    // const fetchProblems = async () => {
    //     const response = await api.get('/problems/');
    //     setProblems(response.data);
    // }

    // =================== TEST DATA ===================
    const problems = [{
        "id": 1,
        "exam": "JEE",
        "difficulty": "Hard",
        "problem": "Abc",
        "type": "MCQ",
        "subject": "Mathematics",
        "category": "Trigonometry"
    },{
        "id": 2,
        "exam": "JEE",
        "difficulty": "Easy",
        "problem": "def",
        "type": "MCQ",
        "subject": "Chemistry",
        "category": "Stoichiometry"
    },{
        "id": 3,
        "exam": "JEE",
        "difficulty": "Medium",
        "problem": "Super long text that no one can possibly ever be bothered to read if I'm being honest, I don't know why anyone would actually be reading this far in.",
        "type": "Subjective",
        "subject": "Physics",
        "category": "Momentum"
    }]
    // ================= TEST DATA END =================

    problems.forEach((problem) => {
        console.log(problem.id);
        console.log(problem.exam);
        console.log(problem.difficulty);
    })

    return (<div>
        <table style={table_style}>
            <thead>
                <tr style={Object.assign({}, {borderBottom: `1px solid ${COLORS.primary}`}, td_th_style)}>
                    <th>Question</th>
                    <th>Subject</th>
                    <th>Difficulty</th>
                    <th>Exam</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
                {problems.map((problem, i) => (
                    <tr style={Object.assign({}, td_th_style, {"background-color": i % 2 ? COLORS["secondary-background"] : COLORS.background})}>
                        <td>{crop(problem.problem)}</td>
                        <td>{problem.subject}</td>
                        <td style={get_colored_string(problem.difficulty)}>{problem.difficulty}</td>
                        <td>{problem.exam}</td>
                        <td>{problem.type}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>)
}

export default App;
