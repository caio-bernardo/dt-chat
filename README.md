#  Monitoring of Conversation Agents with Digital Twin Systems _(dtchat)_

> Framework for building Digital Twins of conversational agents.

This project is part of a larger academic research for **Evaluation of Large Language Models**. The scope of this project is to create a framework or library that allows the creation of applications that monitors conversational agents using the Digital Twin architecture. To accomplish this, a simulated usecase is created to be monitored by the digital twin, this usecase is a chatbot for a imaginary bank, specialized in credit cards. Fake users also will be created to access the chatbot and simulate conversations. Finally, combining process minining techniques, the conversations will produce touchpoints (according to a predefined set, complying to business decision) that will be used to monitor and spin up digital twins for more complex testing and evaluation. 

A schematic of this research is provided below.

![Diagram of monitoring application with digital twins for a chat system powered by a conversational agent](assets/DT-Itau-Model.jpg)


## Project Structure

```sh
dt-chat/
├── apps/
│   └── bancobot/
├── libs/
├── scripts/
```

### Applications _(apps)_

Contains packages to run necessary applications for the simulation.

**bancobot**: Banco Bot, a conversational agent specialized at assisting client from Bank X. See [apps/bancobot](apps/bancobot/README.md) for more.

### Libraries _(lib)_

Contains library code.

### Scripts

Standalone python scripts to run some functionalities, like creating a vector store or reading a database. Each script contains its own set of dependencies and can be run without this project.


## License

This project is under the [MIT License](https://spdx.org/licenses/MIT.html). Check the [License](./LICENSE) for informations about permissions, distribution and modifications.
