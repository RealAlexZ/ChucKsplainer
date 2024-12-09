import subprocess

class ProgrammerAgent:
    def __init__(self, client):
        self.client = client
        self.prompt_template = """
        Let's approach generating ChucK code step by step:

        1. First, analyze the task requirements:
        {task_description}

        2. Break down the audio processing components needed:
        - What UGens (Unit Generators) are required?
        - What signal chain should we create?
        - What parameters need to be configured?

        3. Consider the timing and synchronization:
        - What tempo or timing structures are needed?
        - Are there any event-based triggers required?

        4. Plan the code structure:
        - What variables need to be declared?
        - What functions might be helpful?
        - How should we organize the main loop?

        Based on this analysis, please generate ChucK code that:
        - Is well-commented
        - Uses appropriate UGens and signal chains
        - Handles timing correctly
        - Follows ChucK best practices

        Generate the code:
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
        Let's design comprehensive test cases for this ChucK code task step by step:

        1. Analyze the requirements:
        {task_description}

        2. Consider these testing aspects:
        - Audio output verification
        - Timing accuracy
        - Parameter ranges
        - Edge cases
        - Resource usage

        3. Design test cases that verify:
        - Basic functionality
        - Error handling
        - Performance under different conditions
        - Integration with other UGens

        4. Structure the tests to check:
        - Initial setup
        - Runtime behavior
        - Cleanup and resource management

        Based on this analysis, generate test cases that:
        - Are comprehensive yet focused
        - Include expected outputs
        - Cover edge cases
        - Can be automated

        Generate the test cases:
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