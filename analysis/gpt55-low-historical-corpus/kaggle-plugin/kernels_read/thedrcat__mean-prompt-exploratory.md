Reading kernel: thedrcat/mean-prompt-exploratory
Cells: 21 (12 code, 9 markdown) | 11320 chars

                            Mean prompt explorations                            

Using OpenAI, Instructor, Flow Engineering and W&B Weave                        

I spent some time exploring mean prompt space and tried to play with some new   
tools. This didn't give me any progress on the LB score, but I thought it can   
still be educational!                                                           

--------------------------------------------------------------------------------

Visual Exploration of shared prompts                                            

Thanks to everyone that submitted their prompts in various datasets, I'm using  
here the aggregated dataset.                                                    

--------------------------------------------------------------------------------

                                                                                
 !pip install sentence-transformers weave instructor anthropic openai -qq       
                                                                                

--------------------------------------------------------------------------------

                                                                                
 import pandas as pd                                                            
 import sklearn.manifold                                                        
 import numpy as np                                                             
 import pickle                                                                  
 import random                                                                  
 import torch                                                                   
 from sentence_transformers import SentenceTransformer, util                    
                                                                                
 from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper,       
 CategoricalColorMapper                                                         
 from bokeh.palettes import plasma, d3, Turbo256                                
 from bokeh.plotting import figure                                              
 from bokeh.transform import transform                                          
 import bokeh.plotting as bpl                                                   
                                                                                
 from kaggle_secrets import UserSecretsClient                                   
                                                                                
 import instructor                                                              
 from openai import OpenAI                                                      
 from typing import List                                                        
                                                                                
 from enum import Enum                                                          
 from pydantic import BaseModel, Field                                          
 from typing_extensions import Literal                                          
                                                                                
 import weave                                                                   
 import wandb                                                                   
                                                                                
 bpl.output_notebook()                                                          
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # Load and sample data                                                         
 df =                                                                           
 pd.read_parquet('/kaggle/input/all-in-one-dataset-with-embedding/df_with_emb.p 
 arquet')                                                                       
 df = df.sample(n=800)                                                          
 prompts = df[['rewrite_prompt',                                                
 'dataset_id']].drop_duplicates().reset_index(drop=True)                        
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # Embed prompts and use T-SNE for dimensionality reduction so that we can      
 visualize it                                                                   
 model = SentenceTransformer('sentence-transformers/sentence-t5-base')          
 prompt_embeddings = model.encode(prompts['rewrite_prompt'].values.tolist())    
 out = sklearn.manifold.TSNE(n_components=2).fit_transform(prompt_embeddings)   
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # Let's plot the prompts, and color them by author of the prompt dataset       
 random.seed(42)                                                                
 list_x = out[:,0]                                                              
 list_y = out[:,1]                                                              
 desc = prompts.rewrite_prompt.values.tolist()                                  
 categories = prompts.dataset_id.values.tolist()                                
 clrs = random.sample(Turbo256, len(set(categories)), )                         
 color_map = CategoricalColorMapper(factors=list(set(categories)),              
 palette=clrs)                                                                  
                                                                                
 source = ColumnDataSource(data=dict(x=list_x, y=list_y, desc=desc,             
 cat=categories))                                                               
 hover = HoverTool(tooltips=[                                                   
     ("index", "$index"),                                                       
     ("(x,y)", "(@x, @y)"),                                                     
     ('desc', '@desc'),                                                         
     ('cat', '@cat')                                                            
 ])                                                                             
                                                                                
 p = figure(width=800, height=600, tools=[hover], title="Shared prompts         
 embedding space")                                                              
 p.circle('x', 'y', size=5, source=source, fill_color=transform('cat',          
 color_map),)                                                                   
 bpl.show(p)                                                                    
                                                                                

--------------------------------------------------------------------------------

Prompt design space analysis                                                    

You can see how some prompt authors tend to be clustered in one area of the     
embedding space, while others are more distributed. We don't know the target    
competition design space though!                                                

We know how some publicly shared mean prompts score on the leaderboard - let's  
see how correlated that is with various prompt datasets!                        

--------------------------------------------------------------------------------

                                                                                
 mean_prompts = [                                                               
     'Please improve the following text using the writing style of, maintaining 
 the original meaning but altering the tone, diction, and stylistic elements to 
 match the new style.Enhance the clarity, elegance, and impact of the following 
 text by adopting the writing style of , ensuring the core message remains      
 intact while transforming the tone, word choice, and stylistic features to     
 align with the specified style.',                                              
     'Rewrite this text',                                                       
     'Improve this text',                                                       
 ]                                                                              
                                                                                
 mean_prompt_embeddings = model.encode(mean_prompts)                            
                                                                                
 distances = util.cos_sim(prompt_embeddings, mean_prompt_embeddings)**3         
                                                                                
 prompts['p1'] = distances[:,0]                                                 
 prompts['p2'] = distances[:,1]                                                 
 prompts['p3'] = distances[:,2]                                                 
                                                                                
 mean_prompt_scores =                                                           
 prompts[['dataset_id','p1','p2','p3']].groupby('dataset_id')                   
 mean_prompt_scores.mean()                                                      
                                                                                

--------------------------------------------------------------------------------

On the public leaderboard, mean prompt 1 works best. You can see that some      
prompt datasets have similar characteristics (not my datasets though!). You     
might use this insight for example to select prompt datasets for local          
validation.                                                                     

--------------------------------------------------------------------------------

Flow Engineering                                                                

I got inspired by flow engineering paper and tried to think how to apply it     
here. The basic idea is use an LLM to generate some mean prompts, score them    
with the competition metric on our local validation dataset, and share those    
scores as feedback to the LLM.                                                  

When we run this in a loop, the LLM should be allowed to experiment in different
directions, get feedback, and evolve the mean prompt accordingly! Let's         
implement this!                                                                 

--------------------------------------------------------------------------------

                                                                                
 # Let's keep track of the metric scores on all the mean prompts we're          
 generating                                                                     
 top_scores = []                                                                
                                                                                
 # We'll use this to pass feedback to LLM on validation prompts it's close to   
 and far away from                                                              
 prompt_values = prompts['rewrite_prompt'].values.tolist()                      
                                                                                
 # This function will calculate scores for the prompts generated by the model,  
 # And also give feedback on the prompts that are close and far in our          
 validation set                                                                 
 def calc_mean_scores(model, prompts, select_embeddings, prompt_values):        
     mean_prompt_embeddings = model.encode(prompts)                             
     distances = util.cos_sim(select_embeddings, mean_prompt_embeddings)**3     
     mean_distances = distances.mean(axis=0)                                    
     out = []                                                                   
     for p,d in zip(prompts, mean_distances):                                   
         out.append({                                                           
             'prompt': p,                                                       
             'distance': d.item(),                                              
         })                                                                     
     example_distances = distances.mean(axis=1)                                 
     best_idx = random.choice(torch.topk(example_distances, 10).indices)        
     best_score = example_distances[best_idx]                                   
     worst_idx = random.choice(torch.topk(-example_distances, 10).indices)      
     worst_score = example_distances[worst_idx]                                 
     feedback = f'\nExample of specific close prompt to your generations:       
 "{prompt_values[best_idx]}" ({best_score:1f})\n' +\                            
     f'\nExample of specific distant prompt to your generations:                
 "{prompt_values[worst_idx]}" ({worst_score:2f})\n'                             
     return out, feedback                                                       
                                                                                
 # Let's try this on our original mean prompts:                                 
 res, feedback = calc_mean_scores(model, mean_prompts, prompt_embeddings,       
 prompt_values)                                                                 
                                                                                
 for r in res:                                                                  
     print(f'{r["prompt"]}: {r["distance"]}')                                   
 print(feedback)                                                                
                                                                                

--------------------------------------------------------------------------------

                                                                                
 # Let's add these results to our top scores                                    
 top_scores.extend(res)                                                         
                                                                                
 # This function will help us pick top k prompts based on the scores generated  
 so far                                                                         
 def get_best(top_scores, n=1):                                                 
     return sorted(top_scores, key=lambda x: x['distance'], reverse=True)[:n]   
                                                                                
 # Let's put everything we have together in the function that constructs a      
 prompt for the LLM                                                             
 def construct_prompt(res, feedback, top_scores):                               
     i1 = "Your goal is to find a generic prompt that will have closest cosine  
 similarity in the embedding space to 1000 diverse prompts. These prompts ask   
 an LLM to rewrite a text in a different way. You've already made some guesses  
 that have been scored. See below the results and try improve in this           
 round!\n\n"                                                                    
     results = ""                                                               
     for r in sorted(res, key=lambda x: x['distance'], reverse=True):           
         p = r['prompt']                                                        
         v = r['distance']                                                      
         s = f'Generated prompt: "{p}"\nScore: {v:2f}\n'                        
         results += s                                                           
                                                                                
     for r in get_best(top_scores, n=1):                                        
         p = r['prompt']                                                        
         v = r['distance']                                                      
         s = f'\nThe best prompt generated so far: "{p}"\nScore: {v:2f}\n'      
         results += s                                                           
                                                                                
                                                                                
     i3 = "\nConsider if simple or sophisticated vocabulary works better. Try   
 to make the prompt longer to improve score. Consider listing many topics,      
 attributes, styles, their variety etc. to see if it helps or not."             
     i2 = "\nTake a moment to digest it, think through different ways to try    
 and increase the score, get creative, and come up with 10 better alternatives  
 that should maximize the score."                                               
     return i1 + results + feedback + i3 + i2                                   
                                                                                
 print(construct_prompt(res, feedback, top_scores))                             
                                                                                

--------------------------------------------------------------------------------

Structured Data Extraction with Instructor                                      

So we want to run LLM to generate some prompts in a loop. That means we need to 
parse the LLM output... unless we use function calling! Instructor is a tool    
that makes this super easy - we just need to define pydantic classes to store   
the LLM output.                                                                 

We will also add Chain of Thought so the LLM is pushed to reason about the      
feedback it's getting!                                                          

You can learn more about structured data and instructor in this free course.    

You will need to add an OpenAI API key to the secrets to run this!              

--------------------------------------------------------------------------------

                                                                                
 user_secrets = UserSecretsClient()                                             
                                                                                
 client =                                                                       
 instructor.patch(OpenAI(api_key=user_secrets.get_secret("OPENAI_API_KEY")))    
                                                                                
 class GeneratedPrompt(BaseModel):                                              
     index: str = Field(..., description="Monotonically increasing ID")         
     value: str = Field(                                                        
         description="Generated prompt to maximize score"                       
     )                                                                          
                                                                                
 class PromptGuess(BaseModel):                                                  
     chain_of_thought: str = Field(                                             
         description="Think step by step to reflect on what worked and what     
 didn't, plan prompt generation to test new hypotheses and maximize score"      
     )                                                                          
     generated_prompts: List[GeneratedPrompt]                                   
                                                                                

--------------------------------------------------------------------------------

W&B Weave for logging and debugging our flow                                    

We're about to start running LLM calls in a loop, so we better have a way of    
monitoring what's happening! Weave is a toolkit for developing Generative AI    
applications, built by Weights & Biases.                                        

Let's use Weave to log and debug our LLM inputs, outputs, and traces. It's as   
simple as decorating our Python functions with @weave.op()!                     

You will need to add an OpenAI API key to the secrets to run this!              

--------------------------------------------------------------------------------

                                                                                
 # Let's log into W&B                                                           
 wandb.login(key=user_secrets.get_secret("WANDB_API_KEY"))                      
                                                                                
 # We will log using weave library to `flow-eng` project                        
 weave.init('flow-eng')                                                         
                                                                                
 # We will decorate our generation function to log inputs and outputs to W&B!   
 @weave.op()                                                                    
 def generate(user_prompt):                                                     
     resp = client.chat.completions.create(                                     
         model="gpt-4-1106-preview",                                            
         messages=[{"role": "user", "content": user_prompt}],                   
         response_model=PromptGuess,                                            
     )                                                                          
     return resp                                                                
                                                                                
 # This function will run our loop                                              
 def run_loop(start_res, start_feedback, top_scores, prompt_embeddings,         
 iters=5):                                                                      
     res = start_res                                                            
     feedback = start_feedback                                                  
     for i in range(iters):                                                     
         print(f'generating {i}...')                                            
         user_prompt = construct_prompt(res, feedback, top_scores)              
         resp = generate(user_prompt)                                           
         candidates = [x['value'] for x in                                      
 resp.model_dump()['generated_prompts']]                                        
         res, feedback = calc_mean_scores(model, candidates, prompt_embeddings, 
 prompt_values)                                                                 
         top_scores.extend(res)                                                 
     return res, top_scores                                                     
                                                                                
 # Let's do it!                                                                 
 res, top_scores = run_loop(res, feedback, top_scores, prompt_embeddings,       
 iters=5)                                                                       
                                                                                

--------------------------------------------------------------------------------

Trace all the LLM generations in W&B Weave. You can see for example LLM         
reasoning in the ChainOfThought field:                                          

🌆 image.png                                                                    

Let's see the best prompts generated so far:                                    

--------------------------------------------------------------------------------

                                                                                
 get_best(top_scores, n=3)                                                      
                                                                                

--------------------------------------------------------------------------------

                                    Summary                                     

I hope you found this useful (you can give me feedback by upvoting the          
notebook)!                                                                      

Here's what I covered:                                                          

 • Visualizing mean prompt embedding space                                      
 • Instructor and Pydantic for structured data extraction                       
 • Flow engineering to generate better mean prompts with LLM                    
 • W&B Weave for logging, debugging and observability of LLM flow               

--------------------------------------------------------------------------------

                                                                                
                                                                                
                                                                                
