import subprocess

class ProgrammerAgent:
    def __init__(self, client):
        self.client = client
        self.prompt_template = """
            Generate ChucK code for the following task:
            {task_description}
        """

    def generate_code(self, task_description):
        formatted_prompt = self.prompt_template.format(task_description=task_description)
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ]
        )
        return response.content[0].text.strip()

class TestDesignerAgent:
    def __init__(self, client):
        self.client = client
        self.prompt_template = """
            Generate test cases for the following ChucK code task:
            {task_description}
        """

    def generate_test_cases(self, task_description):
        formatted_prompt = self.prompt_template.format(task_description=task_description)
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ]
        )
        return response.content[0].text.strip()

class TestExecutorAgent:
    def execute_code_with_tests(self, code, test_cases):
        # Save the code and test cases to a temporary file
        with open("temp_code.ck", "w") as f:
            f.write(code)
            f.write("\n")
            f.write(test_cases)

        # Execute the ChucK code and capture the output
        result = subprocess.run(["chuck", "temp_code.ck"], capture_output=True, text=True)

        # Check for errors in the output
        if result.returncode != 0:
            return result.stderr
        return "All tests passed"