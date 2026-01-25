# Userbot

Userbot is simulates a user accessing a conversational agent. It assumes a personality with a specific mission to accomplish at maximum _N_ interactions with the agent. It also allows to simulate time delay, like _thinking_, _word typing_, _breaks/pauses_.

## Features
- Agent to comunicate with other chatbots
- Allows control over thinking, typing speed and chances to take a break, simulating actual human behaivor.

## Prerequistes
- Python 3.12+
- [uv Package Manager](https://docs.astral.sh/uv/)
- OpenAI API Key
- LangSmith API Key (optional, only if you want tracing for your llm model) 

## Install

1. Clone the repository

```sh
git clone https://github.com/caio-bernardo/dt-chat.git
```

2. Install Dependencies

```sh
uv sync --package userbot
```

3. Enviroment Setup

```sh
cp .env.example .env
```

Update the `.env` with your configuration:
- OpenAI API Key
- LangSmith API Key (optional)

## Usage

Create a new `UserBot` object with a prompt engeenering focusing on _who_ the agent is, how it should _act_ and what is its _goal_. Like the following example:

> Você é Alberto Vasconcelos, de 60 anos, residente em João Pessoa (PB). É presidente de uma incorporadora de imóveis de luxo, do segmento Clientes Private Bank. Siga as duas próximas seções: [[como agir]] e [[missão]].
> [[como agir]]
> Adote um estilo de fala direto e impositivo, exigindo respostas rápidas e desconsiderando explicações detalhadas. Seja dominador e inflexível, menosprezando a opinião dos outros e agindo como se suas decisões fossem as únicas corretas. Seja autoritário e ambicioso em suas respostas.
> [[missão]]
> Você está no banco para discutir uma nova oportunidade de investimento. Acredita que sua expertise no mercado imobiliário é superior à dos consultores bancários e espera que eles sigam suas orientações sem questionar. Seu objetivo é impor sua visão e garantir que o banco execute suas ordens rapidamente e sem hesitação.
> Finalize com 'quit' assim que sentir que suas ordens não estão sendo seguidas ou se frustrar com qualquer sinal de discordância ou questionamento.

After that, create a function that interacts with the other chatbot (the target of the user). It should accept a _uuid_ to identify a session and a message of type `HumanMessage`. 

Optionally, you can configure parameter of type `TimeSimulationConfig` and modify:
- word typing speed
- break for thinking
- how often/how much there are pauses
- apply actual delay though sleeps (WARN: it will slow down the application considerably, but provides more realistic results)

See the next section for a example case.

## Testing/Example

There is a simple test/example case in the `tests/` directory. To run the test use:

```sh
uv run --package userbot libs/userbot/tests/run_test.py
``` 

You can also see an actual usecase in [userswarm.py](../../scripts/userswarm.py).

## Built With
- Python 3.12
- uv package manager
- [chatbot library](./chatbot)

## License

This project is licensed under the MIT License -- see the [LICENSE](../../LICENSE) file for details.
