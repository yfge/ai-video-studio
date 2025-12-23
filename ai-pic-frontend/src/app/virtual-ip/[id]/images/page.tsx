import { redirect } from "next/navigation";

interface VirtualIPImagesRedirectProps {
  params: Promise<{ id: string }>;
}

export default async function VirtualIPImagesRedirect({
  params,
}: VirtualIPImagesRedirectProps) {
  const { id } = await params;
  redirect(`/virtual-ip/${id}`);
}
