export default function Loading() {
  return (
    <div className="page-loader fixed inset-0 z-[90] flex items-center justify-center bg-[#0D0D0D]">
      <div className="flex flex-col items-center gap-4">
        <div className="text-xl font-bold text-white">FPL Intelligence</div>
        <div className="flex gap-2">
          <span className="dot-bounce h-2 w-2 rounded-full bg-fpl-green" />
          <span className="dot-bounce h-2 w-2 rounded-full bg-fpl-green [animation-delay:160ms]" />
          <span className="dot-bounce h-2 w-2 rounded-full bg-fpl-green [animation-delay:320ms]" />
        </div>
      </div>
    </div>
  );
}
