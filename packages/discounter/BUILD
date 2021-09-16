python_sources(
	sources=[
		"discounter/*.py"
	],
	dependencies=[":requirements"]
)


python_requirement(
	name="requirements",
	requirements=[
		"fastapi",
		"uvicorn",
		"colorama",
	]
)


pex_binary(
	name="server",
	entry_point="discounter/server.py:main"
)


pex_binary(
	name="server-hotreload",
	entry_point="discounter/server.py:develop",
	restartable=True
)


python_tests(
	name="tests",
	sources=[
		"tests/*.py"
	]
)