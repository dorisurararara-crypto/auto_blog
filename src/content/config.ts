import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
	schema: z.object({
		title: z.string(),
		summary: z.string(),
		image: z.string().optional(),
	}),
});

export const collections = { blog };
