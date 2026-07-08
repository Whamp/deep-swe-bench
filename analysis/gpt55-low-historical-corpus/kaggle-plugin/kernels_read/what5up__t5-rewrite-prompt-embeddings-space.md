Reading kernel: what5up/t5-rewrite-prompt-embeddings-space
Cells: 20 (14 code, 6 markdown) | 11151 chars

 1. 🚀 Supercharge your rewrite_prompt analysis with Sentence Transformers!📚💡 

 • Install dependencies for Sentence Transformers from Kaggle.                  
 • Load essential libraries: pandas, numpy, tqdm, TensorFlow, and Sentence      
   Transformers.                                                                
 • Dive into advanced text processing and analysis effortlessly!                

--------------------------------------------------------------------------------

                                                                                
 # Ref : https://www.kaggle.com/code/cpmpml/sentence-transformers               
                                                                                
 !python -m pip install -q --no-index                                           
 --find-links=../input/sentence-transformers -r                                 
 ../input/sentence-transformers/requirements.txt                                
                                                                                

--------------------------------------------------------------------------------

                                                                                
 import pandas as pd                                                            
 import numpy as np                                                             
 from typing import Iterable                                                    
 import enum                                                                    
 from tqdm.autonotebook import tqdm                                             
 from sentence_transformers import SentenceTransformer, util                    
                                                                                
 import tensorflow_hub as hub                                                   
 import tensorflow as tf                                                        
 import tensorflow_text as text  # Registers the ops.                           
                                                                                
 # https://github.com/tensorflow/tensorflow/issues/35264                        
 gpus = tf.config.experimental.list_physical_devices('GPU')                     
 tf.config.experimental.set_memory_growth(gpus[0], True)                        
                                                                                

--------------------------------------------------------------------------------

    2. 📊 Collect some public prompt data. Embbed and find which part of the    
                    embedding space is well represented.📑🔍                    

 1 Load the aggregated prompts dataset from                                     
   '/kaggle/input/concat-prompts/prompts.csv' which is a collection of prompts  
   from the source datasets 1->7 Here's where to find them! (Check and upvote   
   them for further insights and context.)                                      
 2 Utilize advanced embedding techniques to map prompts into a high-dimensional 
   space.                                                                       
 3 Analyze the distribution of prompts within the embedding space to identify   
   regions with dense representation.                                           
 4 Gain valuable insights into the diversity and coverage of prompt data for    
   text generation tasks.                                                       

--------------------------------------------------------------------------------

                                                                                
 prompt_df = pd.read_csv('/kaggle/input/concat-prompts/prompts.csv')            
 prompt_df                                                                      
                                                                                

--------------------------------------------------------------------------------

                                                                                
 class Backend(enum.Enum):                                                      
     TF = "TF"                                                                  
     TORCH = "TORCH"                                                            
                                                                                
                                                                                
 def embed_text(texts: Iterable[str], backend = Backend("TORCH")) ->            
 np.ndarray:                                                                    
     """                                                                        
     Embed a list of texts using the SentenceTransformer model.                 
     """                                                                        
     if backend == Backend.TORCH:                                               
         embedder =                                                             
 SentenceTransformer("/kaggle/input/sentence-t5-base-hf/sentence-t5-base")      
         return embedder.encode(texts, normalize_embeddings=True)               
     else:                                                                      
         texts    = tf.constant(list(texts))                                    
         embedder =                                                             
 hub.KerasLayer("/kaggle/input/sentence-t5/tensorflow2/st5-base/1")             
                                                                                
         # Define the batch size                                                
         batch_size = 32                                                        
                                                                                
         # Split the texts into batches and embed each batch                    
                                                                                
         embedded_texts = []                                                    
         for i in tqdm(range(0, len(texts), batch_size)):                       
             batch_texts = texts[i:i+batch_size]                                
             embedded_batch = embedder(batch_texts)[0].numpy()                  
             embedded_texts.append(embedded_batch)                              
                                                                                
         return  np.concatenate(embedded_texts, axis=0)                         
                                                                                
                                                                                
                                                                                
 def cosine_cube_similarity(embeddings1: np.ndarray, embeddings2: np.ndarray)   
 -> np.ndarray:                                                                 
     """                                                                        
     Compute the cosine similarity between two sets of embeddings.              
     """                                                                        
     cosine_cube_matrix = np.dot(embeddings1, embeddings2.T)**3                 
     return cosine_cube_matrix                                                  
                                                                                
 def topk_cosine_similarity(                                                    
     query_embeddings: np.ndarray,                                              
     corpus_embeddings: np.ndarray,                                             
     k: int = 5                                                                 
 ) -> np.ndarray:                                                               
     """                                                                        
     Compute the top-k most similar embeddings to the query embeddings.         
     """                                                                        
                                                                                
     cosine_cube_matrix = cosine_cube_similarity(query_embeddings,              
 corpus_embeddings)                                                             
     topk = np.argsort(cosine_cube_matrix, axis=1)[:, -k:]                      
     return topk                                                                
                                                                                
 def botk_cosine_similarity(                                                    
     query_embeddings: np.ndarray,                                              
     corpus_embeddings: np.ndarray,                                             
     k: int = 5                                                                 
 ) -> np.ndarray:                                                               
     """                                                                        
     Compute the bottom-k least similar embeddings to the query embeddings.     
     """                                                                        
     cosine_cube_matrix = cosine_cube_similarity(query_embeddings,              
 corpus_embeddings)                                                             
     botk = np.argsort(cosine_cube_matrix, axis=1)[:, :k]                       
     return botk                                                                
                                                                                
                                                                                
 def create_similarity_df(                                                      
     texts: Iterable[str],                                                      
     embeded_texts = None                                                       
 ) -> pd.DataFrame:                                                             
     """                                                                        
     Create a DataFrame with the top-k most similar prompt instructions.        
     """                                                                        
     if embeded_texts is None:                                                  
         embeded_texts: np.ndarray = embed_text(texts)                          
                                                                                
     cosine_cube_matrix: np.ndarray  = cosine_cube_similarity(embeded_texts,    
 embeded_texts)                                                                 
     topk: np.ndarray = topk_cosine_similarity(embeded_texts, embeded_texts,    
 k=6)                                                                           
     similarities = []                                                          
     for i, similar_indices in enumerate(topk):                                 
         sim_indices = list(similar_indices)                                    
         if i not in sim_indices:                                               
             print(sim_indices)                                                 
             sim_indices = sim_indices[1:]                                      
         else:                                                                  
             sim_indices.remove(i)                                              
         prompt = texts[i]                                                      
         similar_prompts = texts[sim_indices]                                   
         similar_scores = cosine_cube_matrix[i, sim_indices]                    
         similarities.append([prompt] + list(similar_prompts) +                 
 list(similar_scores))                                                          
                                                                                
     similarity_df = pd.DataFrame(similarities, columns=["prompt"] +            
 [f"similar_{i}" for i in range(1, 6)] + [f"score_{i}" for i in range(1, 6)])   
     return similarity_df                                                       
                                                                                
 embeded_texts = embed_text(prompt_df.prompt)                                   
 similarity_df = create_similarity_df(prompt_df.prompt, embeded_texts =         
 embeded_texts)                                                                 
                                                                                

--------------------------------------------------------------------------------

                                                                                
 pd.set_option('display.max_colwidth', 200)                                     
                                                                                
 similarity_df['min_score'] = similarity_df[[f"score_{i}" for i in range(1,     
 6)]].min(axis=1)                                                               
 similarity_df.sort_values(by='min_score', ascending=False)                     
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # PCA Analysis                                                                 
 from sklearn.decomposition import PCA                                          
 import matplotlib.pyplot as plt                                                
 import seaborn as sns                                                          
                                                                                
 n_components = 10                                                              
 # Perform PCA on the embeddings                                                
 pca = PCA(n_components=n_components)                                           
                                                                                
 pca_embeddings = pca.fit_transform(embeded_texts)                              
                                                                                
 # Create a DataFrame with PCA embeddings and minimum cosine scores             
 pca_df = pd.DataFrame(pca_embeddings, columns=[f'PC{k}' for k in range(1,      
 n_components+1)])                                                              
 pca_df['min_score'] = similarity_df['min_score']                               
                                                                                

--------------------------------------------------------------------------------

                                                                                
 import plotly.express as px                                                    
                                                                                
 # Create a DataFrame with PCA embeddings and minimum cosine scores             
 pca_df = pd.DataFrame(pca_embeddings, columns=[f'PC{k}' for k in range(1,      
 n_components+1)])                                                              
 pca_df['min_score'] = similarity_df['min_score']                               
 pca_df['prompt'] = similarity_df['prompt']                                     
                                                                                
 # Plot PCA with color representing minimum cosine score                        
 fig = px.scatter(pca_df, x='PC1', y='PC2', color='min_score',                  
 hover_data=['prompt'],                                                         
                  title='PCA Plot with Representativity')                       
 fig.show()                                                                     
                                                                                

--------------------------------------------------------------------------------

   3. 🔍🤖 Uncover Patterns in Embedded Texts through K-means Clustering! 📊    

 1 Utilize KMeans algorithm from sklearn.cluster to segment embedded texts into 
   5 clusters.                                                                  
 2 Enhance analysis by adding cluster labels to the similarity dataframe.       
 3 Visualize the clustered data in a 3D scatter plot using Plotly, highlighting 
   clusters with different colors.                                              
 4 Explore and interpret the clustering results to gain deeper insights into the
   structure of the text data.                                                  

--------------------------------------------------------------------------------

                                                                                
 from sklearn.cluster import KMeans                                             
                                                                                
 n_clusters = 5                                                                 
                                                                                
 kmeans = KMeans(n_clusters=n_clusters)                                         
 clusters = kmeans.fit_predict(embeded_texts)                                   
                                                                                
 # Add the cluster labels to the similarity dataframe                           
 pca_df['cluster'] = clusters                                                   
 prompt_df['cluster'] = clusters                                                
                                                                                
 # Plot the clusters using Plotly                                               
 fig = px.scatter(pca_df, x='PC1', y='PC2', color='cluster',                    
 hover_data=['prompt'],                                                         
                  title='K-means Clustering')                                   
 fig.show()                                                                     
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # Plot the clusters using Plotly                                               
 fig = px.scatter(pca_df, x='PC2', y='PC3', color='cluster',                    
 hover_data=['prompt'],                                                         
                  title='K-means Clustering')                                   
 fig.show()                                                                     
                                                                                

--------------------------------------------------------------------------------

          4. 🎯🔍 Choose a Representative Prompts for Each Cluster! 💡          

 1 Calculate the centroid for each cluster using the mean of embedded texts     
   belonging to that cluster.                                                   
 2 Normalize the cluster centroids to ensure consistent comparison.             
 3 Identify representative prompts for each cluster by finding the top cosine   
   similarity between each centroid and all embedded texts.                     
 4 Print and store the most representative prompt for each cluster in the       
   representant_dict.                                                           
 5 Gain insights into the characteristics and themes of each cluster through    
   their representative prompts.                                                

--------------------------------------------------------------------------------

                                                                                
 embeded_texts                                                                  
 representant_dict = {}                                                         
 for cluster_id, sdf in prompt_df.groupby('cluster'):                           
     cluster_centroid = np.mean(embeded_texts[sdf.index], axis= 0,              
 keepdims=True)                                                                 
     cluster_centroid = cluster_centroid / np.linalg.norm(cluster_centroid,     
 axis=1, keepdims=True)                                                         
     representant = topk_cosine_similarity(cluster_centroid, embeded_texts,     
 k=1)                                                                           
     print(f'Representant for cluster {cluster_id}:                             
 {prompt_df.loc[representant[0][0], "prompt"]}')                                
     representant_dict[cluster_id] = prompt_df.loc[representant[0][0],          
 "prompt"]                                                                      
                                                                                

--------------------------------------------------------------------------------

                                                                                
 representant_dict                                                              
                                                                                

--------------------------------------------------------------------------------

      5 🔮📝 Predict Prompt Clusters from Output Texts using a Bert Model!      

 1 Load the necessary datasets: sample_submission, test, and train.             
 2 Set up the device for inference, leveraging GPU if available.                
 3 Initialize the tokenizer and the pre-trained model for sequence              
   classification.                                                              
 4 Define a function apply_model to predict the prompt cluster for a given      
   rewritten text.                                                              
 5 Tokenize the rewritten text, pass it through the model, and predict the      
   prompt cluster.                                                              
 6 Handle exceptions gracefully and provide a fallback prompt if prediction     
   fails.                                                                       
 7 Apply the model to each row of the test dataset, generating predicted prompt 
   clusters.                                                                    
 8 Save the predictions to a CSV file named 'submission.csv' containing IDs and 
   corresponding prompt clusters.                                               

--------------------------------------------------------------------------------

                                                                                
 # Infer a model that predict -- prompt_cluster = f(output_text)                
 import pandas as pd                                                            
 from pathlib import Path                                                       
 import numpy as np                                                             
 import torch                                                                   
                                                                                
 COMPETITION_PATH = Path(r"/kaggle/input/llm-prompt-recovery/")                 
 INPUT_PATH = Path(r"/kaggle/input")                                            
                                                                                
 sample_submission = pd.read_csv(COMPETITION_PATH / 'sample_submission.csv')    
 test = pd.read_csv(COMPETITION_PATH / 'test.csv')                              
 train = pd.read_csv(COMPETITION_PATH / 'train.csv')                            
                                                                                
 device = "cuda:0" if torch.cuda.is_available() else "cpu"                      
                                                                                
 from transformers import AutoTokenizer, AutoModelForSequenceClassification     
                                                                                
 tokenizer =                                                                    
 AutoTokenizer.from_pretrained("/kaggle/input/bert-base-promptclusterclassifica 
 tion/bertbase-rewrite-classif")                                                
 model =                                                                        
 AutoModelForSequenceClassification.from_pretrained("/kaggle/input/bert-base-pr 
 omptclusterclassification/bertbase-rewrite-classif").to(device)                
                                                                                
 model.config.id2label = representant_dict                                      
                                                                                
 def apply_model(rewrite_text: str):                                            
     try:                                                                       
         # Tokenize the prompt                                                  
         inputs = tokenizer(rewrite_text, return_tensors="pt").to(device)       
         # Get the model's prediction                                           
         model.eval()                                                           
         with torch.no_grad():                                                  
             outputs = model(**inputs)                                          
             predicted_class_idx = np.argmax(outputs.logits.cpu())              
             predicted_prompt = model.config.id2label[int(predicted_class_idx)] 
             return predicted_prompt                                            
     except:                                                                    
         return "Rewrite this text."                                            
                                                                                
 from tqdm.notebook import tqdm                                                 
 tqdm.pandas()                                                                  
                                                                                
 test['rewrite_prompt'] = test['rewritten_text'].progress_apply(apply_model)    
                                                                                
 test[['id', "rewrite_prompt"]].to_csv('submission.csv', index=False)           
                                                                                

--------------------------------------------------------------------------------

                                                                                
 test                                                                           
                                                                                

--------------------------------------------------------------------------------

Hey everyone,                                                                   

I hope you found this notebook useful! If you did, I'd really appreciate it if  
you could give it an upvote. I'm Wassim, your support means a lot! Thanks a     
bunch! 🙏                                                                       

--------------------------------------------------------------------------------

                                                                                
                                                                                
                                                                                
