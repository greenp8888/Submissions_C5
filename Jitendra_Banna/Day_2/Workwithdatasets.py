from datasets import load_dataset

# Load a dataset (e.g., the SQuAD dataset for question answering)
dataset = load_dataset("squad")

# Print information about the dataset
print(dataset)

# Access an example from the training set
print("\nExample from the training set:")
print(dataset["train"][0])