#!/usr/bin/env python3
"""Score GLP-1 candidate articles for relevance to mesolimbic reward circuitry research question."""

import json
from pathlib import Path

# Scores and rationales for all 126 candidates
SCORES = {
    "pmid:22128031": (5, "Directly maps GLP-1 NTS neuron projections to VTA and NAc, demonstrating mesolimbic reward circuit engagement for food intake control."),
    "pmid:22492036": (5, "Demonstrates exendin-4 reduces food reward value via mesolimbic GLP-1 receptors, directly linking GLP-1 signaling to reward circuitry beyond appetite."),
    "pmid:23219472": (4, "Shows GLP-1 analogue attenuates alcohol-mediated behaviors in rodents, relevant as reward-system analog demonstrating broader reward dampening."),
    "pmid:23874851": (4, "Demonstrates exendin-4 attenuates rewarding properties of psychostimulants, showing GLP-1 effects on non-food reward pathways."),
    "pmid:24105414": (5, "Tests VTA GLP-1R signaling mechanisms for food intake suppression, directly relevant to understanding mesolimbic reward modulation specificity."),
    "pmid:24140429": (5, "Review explicitly addressing GLP-1 roles beyond energy homeostasis in food and drug reward — directly on topic for dissociating appetite from reward."),
    "pmid:24204788": (4, "Shows exendin-4 attenuates nicotine-induced locomotor stimulation and accumbal dopamine release, demonstrating GLP-1 modulation of dopamine reward signaling."),
    "pmid:24560840": (4, "Examines dopamine signaling in amygdala regulated by GLP-1, expanding understanding of GLP-1 reward circuitry beyond VTA/NAc."),
    "pmid:24949661": (5, "Long-term exendin-4 alters expression of both homeostatic and reward markers in brain — directly relevant to dissociating food from reward effects."),
    "pmid:24958205": (4, "Review of appetite-regulating peptides including GLP-1 in addiction pathophysiology, with pharmacotherapy implications."),
    "pmid:26072178": (4, "GLP-1R agonist reduces cocaine self-administration, demonstrating non-food reward dampening via GLP-1 system."),
    "pmid:26211731": (4, "Shows lithium chloride suppresses phasic dopamine via central GLP-1 receptors, mechanistic insight into GLP-1-dopamine interaction in NAc."),
    "pmid:26303264": (4, "Liraglutide attenuates reinforcing properties of alcohol, comparative pharmacology of a clinically used GLP-1 RA on reward."),
    "pmid:26447645": (3, "Liraglutide added to testosterone therapy improves erectile function in diabetic men — relevant to libido/sexual function but mechanism is metabolic improvement, not direct reward."),
    "pmid:27030669": (4, "Review of diverse neural circuitry for GLP-1 weight loss including reward pathways, useful for understanding which circuits are separable."),
    "pmid:27066524": (5, "Directly titled 'GLP-1 influences food and drug reward' — reviews neural substrates shared between food and drug reinforcement via GLP-1."),
    "pmid:27172659": (2, "Liraglutide effect on eNOS in corpus cavernosum of diabetic rats — mechanistic for erectile tissue but peripheral vascular, not reward circuitry."),
    "pmid:28110911": (1, "SUSTAIN 1 phase III trial of semaglutide for T2D glycemic control — pure diabetes efficacy, no reward discussion."),
    "pmid:28266779": (3, "Investigates semaglutide effects on appetite, energy intake, control of eating and food preference — touches on food reward mechanisms beyond simple appetite."),
    "pmid:28323117": (1, "Absorption, metabolism and excretion pharmacokinetics of semaglutide — no neurological relevance."),
    "pmid:29337226": (4, "Review of GLP-1 signaling and alcohol-mediated behaviors with preclinical and clinical evidence — strong reward-system relevance."),
    "pmid:29363040": (1, "Semaglutide first global approval review — regulatory/clinical overview without reward mechanism discussion."),
    "pmid:29397376": (1, "SUSTAIN 7 head-to-head semaglutide vs dulaglutide for T2D — pure efficacy comparison without neurological discussion."),
    "pmid:30615985": (1, "Comparative efficacy/safety/cardiovascular outcomes of semaglutide in T2D — no reward discussion."),
    "pmid:30771711": (5, "Brain region-specific GLP-1R effects on alcohol intake in rodents — directly addresses regional specificity of reward modulation, key for dissociability question."),
    "pmid:31539622": (1, "SUSTAIN 10 semaglutide vs liraglutide efficacy/safety in T2D — clinical efficacy without reward mechanism content."),
    "pmid:31593982": (3, "Insula-to-ventral-striatum projections in compulsive eating — relevant circuit for understanding reward-driven eating though not GLP-1 specific."),
    "pmid:31759971": (4, "Review of alcohol-mediated behaviors and gut-brain axis with GLP-1 focus — substantive on reward mechanisms."),
    "pmid:31821815": (5, "Phasic dopamine responses to food cues suppressed by exendin-4 — directly measures GLP-1 RA effects on reward prediction signaling."),
    "pmid:32026771": (3, "Hippocampal inhibitory learning in eating and drug taking — discusses shared mechanisms but GLP-1 is not the primary focus."),
    "pmid:32213703": (4, "Semaglutide reduces body weight via distributed neural pathways — identifies specific brain regions including reward areas activated by semaglutide."),
    "pmid:32450068": (5, "Exendin-4 reduces sexual interaction behaviors in brain site-specific manner — directly addresses GLP-1 RA effects on libido/sexual reward, essential for dissociability question."),
    "pmid:33269530": (3, "Semaglutide 2.4mg effects on appetite, control of eating, and energy intake — relevant for understanding dose-dependent appetite/reward modulation."),
    "pmid:33352692": (5, "Brain site-specific inhibitory effects of exendin-4 on alcohol intake and operant responding for palatable food — directly tests regional dissociation of GLP-1 reward effects."),
    "pmid:33667417": (2, "STEP 2 trial of semaglutide for weight loss in T2D — efficacy focus without mechanistic reward discussion."),
    "pmid:33741445": (4, "Review of GLP-1 analogues for stress-related eating and GLP-1 role in stress, emotion, mood — addresses psychiatric/motivational dimensions of GLP-1."),
    "pmid:33969456": (1, "Clinical pharmacokinetics of oral semaglutide — pure PK without neurological content."),
    "pmid:34248838": (1, "Efficacy of semaglutide subcutaneous and oral formulations for T2D — clinical efficacy review."),
    "pmid:34260945": (2, "Structural biology of semaglutide-bound GLP-1R-Gs complexes — receptor pharmacology but at molecular level, not circuit level."),
    "pmid:34293304": (1, "SUSTAIN FORTE semaglutide 2.0 vs 1.0 mg for T2D — dose comparison for glycemic control, not neurological."),
    "pmid:34305810": (2, "Safety review of semaglutide — includes side effect profiles but focuses on GI/metabolic rather than reward/neurological."),
    "pmid:34706925": (2, "Wegovy overview for weight loss — general review mentions mechanism of action but lacks depth on reward circuitry."),
    "pmid:34942372": (2, "Semaglutide for obesity treatment review — mentions mechanisms but focused on weight loss efficacy."),
    "pmid:34955726": (4, "Overview of appetite-regulatory peptides in addiction — systematic review covering GLP-1 among multiple peptide systems in reward/addiction."),
    "pmid:35131037": (1, "STEP trial of semaglutide for weight management in East Asian population — regional efficacy study."),
    "pmid:35300299": (4, "Reviews possible mechanisms of GLP-1R agonist effects on cocaine use disorder — directly examines reward pathway mechanisms."),
    "pmid:36063105": (2, "GLP-1R in dentate gyrus mossy cells — interesting for GLP-1 brain function but focused on hippocampal learning, not reward circuitry."),
    "pmid:36568109": (1, "Semaglutide in NAFLD mouse model — liver/metabolic outcomes, no reward content."),
    "pmid:36578889": (1, "Meta-analysis of semaglutide weight loss efficacy in non-diabetic obesity — pure efficacy."),
    "pmid:36699502": (4, "Review of gut-brain axis in alcohol with focus on GLP-1, amylin, ghrelin — substantive on reward mechanisms."),
    "pmid:36706596": (1, "Semaglutide inhibits cardiomyocyte apoptosis — cardiovascular mechanism, no reward content."),
    "pmid:37030441": (2, "FGF21 required for liraglutide weight loss — metabolic mechanism without reward focus."),
    "pmid:37063267": (4, "Review of GLP-1 therapeutic potential for addiction based on preclinical and clinical findings — comprehensive reward-related coverage."),
    "pmid:37099334": (2, "JAMA news article on Ozempic popularity — general information without mechanistic depth."),
    "pmid:37148870": (4, "GLP-1 and nicotine combination therapy engages hypothalamic and mesolimbic pathways — shows crosstalk between GLP-1 and nicotinic reward circuits."),
    "pmid:37178855": (5, "Review of metabolic hormone action in VTA for reward-directed behavior — directly examines how GLP-1 and other hormones modulate reward in VTA."),
    "pmid:37192005": (5, "Semaglutide reduces alcohol drinking and modulates central GABA neurotransmission — demonstrates specific neurotransmitter mechanism for GLP-1 RA reward modulation."),
    "pmid:37295046": (4, "Semaglutide reduces alcohol intake and relapse-like drinking — clinically relevant GLP-1 RA with dose-response data on reward behavior."),
    "pmid:37640171": (1, "Semaglutide and cardiovascular disease from SELECT trial — pure cardiovascular."),
    "pmid:37672701": (1, "Semaglutide in early Type 1 diabetes — letter, no reward content."),
    "pmid:37688299": (1, "Semaglutide and pregnancy — no reward content."),
    "pmid:38549620": (5, "Exendin-4 disrupts responding to reward-predictive incentive cues — directly tests GLP-1 RA effects on cue-driven reward behavior, central to food noise question."),
    "pmid:38555109": (1, "Meta-analysis of acute pancreatitis risk with semaglutide — safety without reward content."),
    "pmid:38561101": (3, "Liraglutide relieves depressive symptoms via neurogenesis and inflammation reduction — relevant to mood/motivation effects of GLP-1 RAs."),
    "pmid:38574433": (1, "Semaglutide attenuates doxorubicin cardiotoxicity — cardioprotection mechanism, no reward."),
    "pmid:38579490": (4, "Review of neurocircuitry for GLP-1 and PYY in suppression of food, drug-seeking, and related behaviors — comprehensive circuit-level analysis."),
    "pmid:38613667": (1, "Network meta-analysis tirzepatide vs semaglutide for T2D — efficacy comparison without reward mechanisms."),
    "pmid:38629387": (1, "Systematic review of semaglutide effects on lean mass — body composition focus."),
    "pmid:38774967": (1, "Semaglutide for obesity in adolescents — pediatric weight management."),
    "pmid:38778151": (4, "Semaglutide prescribing associated with increased erectile dysfunction risk — directly quantifies sexual dysfunction side effect, key for reward dampening question."),
    "pmid:38887265": (2, "Lateral parabrachial nucleus astrocytes control food intake — brain region relevant to feeding but not GLP-1 or reward specific."),
    "pmid:38928616": (5, "Explores GLP-1 RA impact on substance use, compulsive behavior, AND libido — directly addresses whether reward dampening extends beyond appetite to sexual function."),
    "pmid:38945189": (4, "Systematic review of GLP-1 agonist effects on reward behavior — comprehensive coverage of reward modulation evidence."),
    "pmid:38952487": (1, "Clinical pharmacokinetics of semaglutide systematic review — PK without neurological content."),
    "pmid:38958939": (1, "Semaglutide and optic neuropathy risk — ophthalmologic safety."),
    "pmid:39032839": (5, "IUPHAR review of GLP-1 as pharmacotherapeutic target for substance use disorders — authoritative review of GLP-1 in reward/addiction with therapeutic perspective."),
    "pmid:39046272": (1, "Meta-analysis of semaglutide safety profile — general safety without reward specificity."),
    "pmid:39180919": (1, "Heat stress effects on broiler feeding preference — animal husbandry, completely unrelated."),
    "pmid:39389039": (4, "Review of gut hormones as possible mediators of addictive disorders — covers GLP-1 among reward-modulating peptides."),
    "pmid:39445596": (2, "Semaglutide association with Alzheimer's disease diagnosis — neurodegeneration focus, not reward circuitry."),
    "pmid:39515485": (4, "Systematic review of GLP-1 mono-agonist effects on brain functional connectivity — directly examines neural target engagement relevant to reward networks."),
    "pmid:39529123": (3, "GLP-1 RAs for nicotine cessation in psychiatric populations — relevant intersection of reward modulation and psychiatric symptoms."),
    "pmid:39551458": (3, "Semaglutide effects on testicular dysfunction and spermatogenesis in diabetic rats — relevant to sexual function side effects though mechanism is metabolic."),
    "pmid:39639536": (4, "GLP-1 and amylin receptor agonist combination reduces alcohol consumption — comparative pharmacology of combined agonists on reward behavior."),
    "pmid:39743126": (4, "Review of tirzepatide and semaglutide for obesity-related diseases and addictions — comparative pharmacology of different GLP-1 compounds on reward."),
    "pmid:39818408": (4, "Compares addiction risk between bariatric surgery (increased) and GLP-1 RAs (reduced) — directly relevant to whether GLP-1 RAs dampen reward broadly."),
    "pmid:39964126": (3, "GLP-1 and GIP receptor agonist effects on neurogenesis and psychiatric applications — touches on mood/motivation effects."),
    "pmid:40184508": (1, "Meta-analysis tirzepatide vs semaglutide weight loss in T2D — efficacy comparison."),
    "pmid:40240532": (4, "Cross-sectional analysis of male sexual dysfunction associated with GLP-1 RAs from FAERS data — directly quantifies sexual side effects across GLP-1 RA class."),
    "pmid:40245495": (5, "Inhibitory GLP-1 circuit in lateral septum modulates reward processing and alcohol intake — identifies specific circuit for GLP-1 reward modulation, key for dissociability."),
    "pmid:40302255": (4, "Emerging therapeutics for SUDs focusing on GLP-1R agonists, D3R antagonists — comparative pharmacology for reward modulation."),
    "pmid:40388988": (3, "Ultra-processed food effects on hedonic and homeostatic appetite — relevant context for understanding food noise and reward eating though not GLP-1 specific."),
    "pmid:40456683": (5, "GLP-1R/Y-receptor triple agonist decreases fentanyl-evoked dopamine in NAc — tests novel compound for selective reward modulation, directly relevant to alternative compound strategies."),
    "pmid:40458885": (1, "Semaglutide for cardiovascular-kidney-metabolic syndrome — metabolic focus."),
    "pmid:40487373": (4, "Tirzepatide effects on sexual function in women — case report directly relevant to sexual dysfunction from GLP-1-class drug."),
    "pmid:40508146": (5, "Review of GLP-1 analogues in neurobiology of addiction with translational insights — comprehensive mechanistic and therapeutic perspective on reward modulation."),
    "pmid:40614622": (3, "Tirzepatide association with erectile dysfunction compared to other agents — comparative data on sexual dysfunction across GLP-1 class."),
    "pmid:40616879": (4, "Novel pharmacological approaches for eating disorders comorbid with SUDs — addresses shared reward mechanisms and GLP-1 as potential treatment."),
    "pmid:40635383": (4, "Systematic review of GLP-1 RA efficacy for psychiatric symptoms — directly examines mood, motivation, and behavioral effects beyond metabolism."),
    "pmid:40666108": (5, "Case report of anorgasmia following GLP-1 agonist initiation — direct clinical evidence of sexual reward dampening from GLP-1 RA."),
    "pmid:40722294": (3, "GLP-1 RAs as new frontier in treating AUD — reviews reward mechanisms but likely overlaps substantially with other included reviews."),
    "pmid:40843757": (5, "Review of GLP-1 mechanisms in modulating craving and addiction with neurobiological insights — directly addresses how GLP-1 RAs affect reward processing."),
    "pmid:40886075": (1, "Semaglutide and tirzepatide in HFpEF patients — cardiology focus."),
    "pmid:40916127": (4, "Review of GLP-1 brain mechanisms beyond metabolic effects — directly examines non-metabolic neurological actions."),
    "pmid:40985188": (4, "Neuroendocrinology meets addiction — emerging pharmacotherapies including GLP-1 RAs for substance use disorders."),
    "pmid:41008590": (4, "Review of GLP-1 RA impact on erectile function — comprehensive analysis of sexual dysfunction mechanisms."),
    "pmid:41015576": (4, "Crosstalk between AUD and obesity — examines shared neurobiological mechanisms relevant to understanding whether GLP-1 modulates overlapping reward circuits."),
    "pmid:41092926": (1, "Global Burden of Disease study — epidemiology, completely unrelated."),
    "pmid:41253199": (5, "Review titled 'Psychotropic effects of GLP-1R agonists' — directly examines psychiatric and behavioral effects including potential anhedonia and mood changes."),
    "pmid:41303457": (4, "GLP-1 RA therapeutic potential for binge eating disorder — examines reward mechanisms specific to compulsive eating behavior."),
    "pmid:41427954": (5, "Review titled 'Beyond metabolism: sexual dysfunction and weight-loss drugs' — directly examines sexual dysfunction from GLP-1 RAs and related drugs."),
    "pmid:41498523": (3, "GLP-1 RA effects on male reproductive hormones, semen parameters — relevant to sexual/endocrine effects but more metabolic than reward-focused."),
    "pmid:41512288": (3, "Patient perceptions of Ozempic for weight loss from online reviews — may capture reports of food noise reduction, mood changes, and sexual effects from real users."),
    "pmid:41552827": (4, "Systematic review of GLP-1 RAs in substance use disorders — comprehensive evidence synthesis on reward modulation."),
    "pmid:41716526": (2, "GLP-1 RA effects on urological health case reports — peripheral effects, limited reward circuitry content."),
    "pmid:41753300": (3, "Incretin-based therapies in addiction treatment — relevant overview but likely less mechanistically deep than other included reviews."),
    "pmid:41794143": (3, "Sugar addiction at crossroads of reward, metabolism, and culture — contextually relevant for understanding food noise and hedonic eating."),
    "pmid:41870138": (5, "GLP-1 RA effects on sexual function in women and men — narrative review directly addressing the sexual reward dampening question."),
    "arxiv:1304.4201": (2, "Reward and adversity processing circuits with dopamine/serotonin — relevant framework but no GLP-1 content."),
    "arxiv:2603.14597": (1, "AI agent memory architecture inspired by dopamine — computational, not pharmacological."),
    "arxiv:2108.12402": (1, "Computational model of reward prediction errors — machine learning, not pharmacological."),
    "arxiv:2603.12341": (3, "Self-reported side effects of semaglutide/tirzepatide from Reddit — may capture real-world reports of reward dampening, mood changes, sexual effects."),
    "arxiv:0706.1293": (1, "Anhedonia in mice from social stress — no GLP-1 content, general depression model."),
    "arxiv:2404.01358": (3, "AI analysis of GLP-1 RA adverse side effects from social media — may identify reward-related and sexual side effects from large-scale data."),
    "pmid:28595561": (2, "Review of sexual dysfunction and cardiovascular risk with pharmacotherapy — general overview without specific GLP-1 reward mechanism content."),
    "pmid:29049653": (1, "Phase II trial comparing oral vs subcutaneous semaglutide for T2D glycemic control — pure diabetes efficacy, no reward discussion."),
}

def main():
    input_path = Path("data/staged/glp1_candidates_prefiltered.json")
    output_path = Path("data/staged/glp1_scored.json")

    with open(input_path) as f:
        candidates = json.load(f)

    scored = 0
    included = 0
    excluded = 0
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for item in candidates:
        item_id = item["item_id"]
        if item_id in SCORES:
            score, rationale = SCORES[item_id]
            item["relevance_score"] = score
            item["inclusion_rationale"] = rationale
            item["included"] = score >= 3
            scored += 1
            distribution[score] += 1
            if score >= 3:
                included += 1
            else:
                excluded += 1
        else:
            print(f"WARNING: No score for {item_id}")

    with open(output_path, "w") as f:
        json.dump(candidates, f, indent=2)

    print(f"\n{'='*60}")
    print(f"GLP-1 Reward Circuitry Research — Scoring Summary")
    print(f"{'='*60}")
    print(f"Total scored:  {scored}")
    print(f"Included (>=3): {included}")
    print(f"Excluded (<3):  {excluded}")
    print(f"\nScore distribution:")
    for score in range(1, 6):
        bar = "#" * distribution[score]
        label = {1: "Not relevant", 2: "Tangential", 3: "Moderate", 4: "Highly relevant", 5: "Essential"}[score]
        print(f"  {score} ({label:>16}): {distribution[score]:3d}  {bar}")
    print(f"\nOutput saved to: {output_path}")


if __name__ == "__main__":
    main()
