import type { SVGProps } from 'react';
import { memo } from 'react';
const SvgAzurePower = (props: SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={18} height={18} viewBox="0 0 18 18" {...props}>
    <defs>
      <radialGradient
        id="bf0e6238-d7a1-45b5-861c-8bbe56952eb1"
        cx={3.117}
        cy={-116.12}
        r={9.022}
        gradientTransform="translate(5.844 100.656) scale(1.013 0.789)"
        gradientUnits="userSpaceOnUse"
      >
        <stop offset={0.196} stopColor="#ffd70f" />
        <stop offset={0.438} stopColor="#ffcb12" />
        <stop offset={0.873} stopColor="#feac19" />
        <stop offset={1} stopColor="#fea11b" />
      </radialGradient>
    </defs>
    <title>{'MsPortalFx.base.images-37'}</title>
    <g id="b6078d51-b129-4cd0-9a4d-e8ff551d4747">
      <path
        d="M8.09,10.01H3.464a.239.239,0,0,1-.262-.2.175.175,0,0,1,.023-.085L8.775.12A.274.274,0,0,1,9.014,0h5.47a.238.238,0,0,1,.262.2A.177.177,0,0,1,14.7.319L8.186,7.834h6.35a.239.239,0,0,1,.262.2.185.185,0,0,1-.067.137L4.175,17.788c-.1.051-.8.562-.458-.214h0Z"
        fill="url(#bf0e6238-d7a1-45b5-861c-8bbe56952eb1)"
      />
    </g>
  </svg>
);
const Memo = memo(SvgAzurePower);
export default Memo;
