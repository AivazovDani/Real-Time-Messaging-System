from typing import Optional
from fastapi import FastAPI, Path
from pydantic import BaseModel


app = FastAPI(title="Test")

students = {
    1:{
        "name": "John",
        "age": 17,
        "year": "Year 11"
    }
}

class Student(BaseModel):
    name: str
    age: int
    year: str


class UpdateStudent(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    year: Optional[str] = None



@app.get("/")
def main():
    pass


@app.get("/get-student/{student_id}") # /get-student/1 - path parameter
def get_student(student_id:int = Path(None, description="The ID of the student you want to view", gt=0, lt=5)):
    return students[student_id]


@app.get("/get-by-name") # query parameter
def get_student(*, name: Optional[str] = None, age:int):
    for student_id in students:
        if students[student_id]['name'] == name:
            return students[student_id]
        
        return {"Data": "Not Found"}


@app.post("/create-student/{student_id}")
def create_student(student_id: int, student: Student):
    if student_id in students:
        return {"Error": "Student already exists man"}
    
    students[student_id] = student
    return students[student_id]




@app.put("/update-student/{student_id}")
def update_student(student_id: int, student = UpdateStudent):
    if student_id not in student:
        return {"Error": "Student does not exists"}
    
    if student.name != None:
        
        students[student_id].name = student.name

    if student.age != None:
        student[student_id].age = student.age

    if student.year != None:
        student[student_id].year = student.year
        
        
        
    return student[student_id]



@app.delete("/delete-student/{student_id}")
def delete_student(student_id: int):
    if student_id not in students:
        return {"Error": "Student does not exists my good man broski boy yea"}
    
    del students[student_id]
    return {"Message": "Student deleted sucessfully"}


# if __name__ == "__main__":
#     main()

