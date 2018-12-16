from deeppavlov import configs, build_model
from deeppavlov import train_model

class NER:

    ner_model = build_model("./deeppavlov/ner_config.json", download=True)

    def train():
        train_model("./deeppavlov/ner_config.json", download=True)
        NER.ner_model = build_model("./deeppavlov/ner_config.json", download=True)

    def NamedEntityRecognition(message):
        ner = NER.ner_model([message])
        return ner[0][0], ner[1][0]

if __name__ == "__main__":
    msg = 'I want to watch an action film with Arnold Swarzenneger'
    NER.train()
    msg_split, ner_labels = NER.NamedEntityRecognition(msg)
    print(msg_split)
    print(ner_labels)
