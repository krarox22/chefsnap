import { apiClient } from "./client";

export interface DetectedIngredient {
  name: string;
  display_name: string;
  confidence: number;
  quantity_hint: string;
}

export interface DetectResponse {
  ingredients: DetectedIngredient[];
  unrecognized_regions: number;
  request_id: string;
  allergen_warnings?: string[];
}

export async function detectIngredients(
  photoUris: string[],
  locale = "en-IN"
): Promise<DetectResponse> {
  const formData = new FormData();
  photoUris.forEach((uri, i) => {
    formData.append("files", {
      uri,
      name: `photo_${i}.jpg`,
      type: "image/jpeg",
    } as unknown as Blob);
  });

  const { data } = await apiClient.post<DetectResponse>(
    `/api/v1/ingredients/detect?locale=${locale}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}
