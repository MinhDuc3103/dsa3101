from utils.classes import RubricItem


def marks_by_question(
    rubric_data, rubric_scheme_data, student_num_file_map, student_num=None
):
    marks_by_question = {}

    for file_idx, questions in rubric_data.items():
        if student_num and student_num_file_map[file_idx] != student_num:
            continue

        for question_num, total_marks in sorted(
            rubric_scheme_data["questions"].items(), key=lambda x: int(x[0])
        ):
            question = int(question_num)
            if question_num in questions:
                marks_deductions = sum(
                    int(RubricItem.from_dict(item).marks)
                    for item in questions[question_num]
                )
            else:
                marks_deductions = 0

            final_marks = total_marks + marks_deductions
            if question not in marks_by_question:
                marks_by_question[question] = [final_marks]
            else:
                marks_by_question[question].append(final_marks)

    return marks_by_question


def student_total_marks(
    rubric_data, rubric_scheme_data, student_num_file_map=None, student_num=None
):
    all_marks = []
    total_marks = rubric_scheme_data["total"]

    for file_idx, pages in rubric_data.items():
        if (
            student_num_file_map
            and student_num
            and student_num_file_map[file_idx] != student_num
        ):
            continue

        marks_deductions = sum(
            sum(int(RubricItem.from_dict(item).marks) for item in page)
            for page in pages.values()
        )
        final_marks = total_marks + marks_deductions

        all_marks.append(final_marks)

    return all_marks
