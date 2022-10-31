from utils.classes import RubricItem


def marks_by_question(rubric_data, grading_data, student_num=None):
    marks_by_question = {}

    for file_idx, pages in rubric_data.items():
        if student_num and grading_data[file_idx]["student_num"] != student_num:
            continue

        for page_idx, rubric_items in sorted(pages.items(), key=lambda x: int(x[0])):
            question = int(grading_data[file_idx][page_idx]["question_num"])
            question_marks = sum(
                int(RubricItem.from_dict(item).marks) for item in rubric_items
            )
            if question not in marks_by_question:
                marks_by_question[question] = [question_marks]
            else:
                marks_by_question[question].append(question_marks)

    return marks_by_question


def student_total_marks(rubric_data, grading_data=None, student_num=None):
    all_marks = []

    for file_idx, pages in rubric_data.items():
        if (
            grading_data
            and student_num
            and grading_data[file_idx]["student_num"] != student_num
        ):
            continue

        total_marks = sum(
            sum(int(RubricItem.from_dict(item).marks) for item in page)
            for page in pages.values()
        )

        all_marks.append(total_marks)

    return all_marks
