from deeppavlov import configs, build_model
from deeppavlov import train_model

class NER:

    def __init__(self, train=False):
        if train:
            train_model("./deeppavlov/ner_config.json", download=True)
        self.ner_model = build_model("./deeppavlov/ner_config.json", download=True)

    def NamedEntityRecognition(self, message):
        ner = self.ner_model([message])
        return ner[0][0], ner[1][0]

if __name__ == "__main__":
    ner = NER(train=False)
    msg = 'I want to watch an action film with Arnold Swarzenneger'
    msg_split, ner_labels = ner.NamedEntityRecognition(msg)
    print(msg_split)
    print(ner_labels)
