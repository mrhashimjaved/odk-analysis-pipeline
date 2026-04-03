library(lme4)

df <- read.csv("data/your_combined_data.csv")

model <- lmer(apq_involvement ~ time * group + (1|participant_id), data=df)

sink("output/results.txt")
summary(model)
sink()