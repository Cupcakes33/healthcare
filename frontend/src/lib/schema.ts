import { z } from "zod";

export const questionnaireSchema = z.object({
  age: z
    .number({ message: "나이를 입력해주세요" })
    .int("정수로 입력해주세요")
    .min(1, "1세 이상이어야 합니다")
    .max(150, "150세 이하여야 합니다"),
  gender: z.enum(["M", "F"], { message: "성별을 선택해주세요" }),
  symptoms: z
    .array(z.string())
    .min(1, "증상을 1개 이상 선택해주세요"),
  duration: z.string().min(1, "증상 지속 기간을 선택해주세요"),
  existingConditions: z.array(z.string()),
});

export type QuestionnaireSchema = z.infer<typeof questionnaireSchema>;
